"""Reliable serial transport for the StreamDeck hardware.

The controller deliberately owns all transport lifecycle details.  A successful
``connect`` starts exactly one reader and one command worker; a transport error is
recovered by that same reader rather than by recursively creating new workers.
"""

from __future__ import annotations

import queue
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

try:  # Importing the application should not require attached hardware.
    import serial
    import serial.tools.list_ports
except ImportError:  # pragma: no cover - exercised on installations without pyserial
    serial = None  # type: ignore[assignment]


class SerialController:
    """Manage the serial connection to a StreamDeck-compatible device.

    Callbacks are invoked outside controller locks.  They may therefore call back
    into this object safely, but run on a controller worker thread and must marshal
    UI work to the GUI thread themselves.

    In addition to the legacy events, ``connection_state`` is emitted with one
    boolean argument whenever the effective connection state changes.
    """

    RESET_DELAY = 2.0
    HELLO_TIMEOUT = 1.0
    LEGACY_START_TIMEOUT = 3.0
    STOP_TIMEOUT = 1.0
    READ_POLL_INTERVAL = 0.02
    COMMAND_POLL_INTERVAL = 0.1
    RECONNECT_INITIAL_DELAY = 0.25
    RECONNECT_MAX_DELAY = 5.0
    MAX_LINE_LENGTH = 4096

    _QUEUE_STOP = object()

    def __init__(self, port: str = None, baud_rate: int = 9600, logger=None):
        self.port = port
        self.baud_rate = baud_rate
        self.ser = None
        self.connected = False
        self.logger = logger

        self.last_data = ""
        self.protocol_version: Optional[int] = None
        self.firmware_version: Optional[str] = None
        self.capabilities: Dict[str, str] = {}

        self.callbacks: Dict[str, List[Callable[..., Any]]] = {}
        self._callback_lock = threading.RLock()
        self._state_lock = threading.RLock()
        self._lifecycle_lock = threading.RLock()
        self._io_lock = threading.RLock()

        self._listener_thread: Optional[threading.Thread] = None
        self._stop_listener = threading.Event()
        self._command_thread: Optional[threading.Thread] = None
        self._stop_command = threading.Event()

        # Separate FIFO queues preserve the legacy priority behaviour while using
        # thread-safe queue.Queue rather than a list guarded by polling locks.
        self._command_queue: "queue.Queue[object]" = queue.Queue()
        self._priority_command_queue: "queue.Queue[object]" = queue.Queue()
        self._deferred_lines: "queue.Queue[str]" = queue.Queue()

    def log(self, level: str, message: str) -> None:
        """Log a message when the supplied logger supports *level*."""
        if self.logger and hasattr(self.logger, level):
            getattr(self.logger, level)(message)

    def list_ports(self) -> List[Tuple[str, str]]:
        """Return available ``(port, description)`` pairs."""
        if serial is None:
            self.log("error", "pyserial is not installed")
            return []
        try:
            return [
                (port.device, port.description)
                for port in serial.tools.list_ports.comports()
            ]
        except Exception as exc:
            self.log("error", f"Failed to enumerate serial ports: {exc}")
            return []

    def connect(self) -> bool:
        """Connect and start the two controller workers exactly once."""
        with self._lifecycle_lock:
            if self.is_connected():
                self._ensure_workers_locked()
                return True
            if not self.port:
                self.log("error", "Cannot connect: No port specified")
                return False
            if serial is None:
                self.log("error", "Cannot connect: pyserial is not installed")
                return False

            # A stale worker from an interrupted lifecycle must be stopped before a
            # fresh explicit connection is established.
            if not self._stop_workers_locked():
                self.log("error", "Cannot connect while old serial workers are stopping")
                return False
            self._stop_listener.clear()
            self._stop_command.clear()

            if not self._open_and_handshake(self._stop_listener):
                self._close_transport()
                self._set_connected(False)
                return False

            self._set_connected(True)
            self._ensure_workers_locked()
            self.log("info", f"Connected to StreamDeck on {self.port}")
            return True

    def disconnect(self) -> None:
        """Stop workers, stop the device and close the port deterministically."""
        with self._lifecycle_lock:
            had_transport = self.ser is not None
            self._stop_listener.set()
            self._stop_command.set()
            self._wake_command_worker()
            listener_stopped = self._join_worker(self._listener_thread)
            command_stopped = self._join_worker(self._command_thread)
            if listener_stopped:
                self._listener_thread = None
            if command_stopped:
                self._command_thread = None

            # No reader can steal the acknowledgement after the worker join.
            if had_transport and self.is_connected():
                self.stop_device()
            self._close_transport()
            self._set_connected(False)
            self._clear_queue(self._command_queue)
            self._clear_queue(self._priority_command_queue)
            self._clear_queue(self._deferred_lines)
            if had_transport:
                self.log("info", "Disconnected from StreamDeck")

    def reconnect(self) -> bool:
        """Perform an explicit clean reconnect without recursive worker creation."""
        self.disconnect()
        return self.connect()

    def start_device(self) -> bool:
        """Negotiate protocol v1, falling back to the legacy start handshake."""
        if self.ser is None:
            return False

        try:
            with self._io_lock:
                self.protocol_version = None
                self.firmware_version = None
                self.capabilities = {}

                self.ser.write(b"HELLO 1\n")
                ready = self._wait_for_response_locked(
                    lambda line: line.startswith("READY "),
                    self.HELLO_TIMEOUT,
                    self._stop_listener,
                )
                if ready is not None and self._parse_ready(ready):
                    self.ser.write(b"START\n")
                    started = self._wait_for_response_locked(
                        lambda line: line == "ACK START",
                        self.LEGACY_START_TIMEOUT,
                        self._stop_listener,
                    )
                    if started == "ACK START":
                        return True
                    self.log("warning", "Protocol v1 device did not acknowledge START")
                    return False

                self.ser.write(b"start\n")
                legacy = self._wait_for_response_locked(
                    lambda line: line == "start ok",
                    self.LEGACY_START_TIMEOUT,
                    self._stop_listener,
                )
                if legacy == "start ok":
                    self.protocol_version = 0
                    return True

            self.log("error", "Device did not answer HELLO or legacy start handshake")
            return False
        except Exception as exc:
            self.log("error", f"Error starting device: {exc}")
            return False

    def stop_device(self) -> bool:
        """Ask the connected device to stop and wait briefly for acknowledgement."""
        if self.ser is None or not self.is_connected():
            return False
        try:
            with self._io_lock:
                if self.protocol_version and self.protocol_version >= 1:
                    self.ser.write(b"STOP\n")
                    response = self._wait_for_response_locked(
                        lambda line: line == "ACK STOP",
                        self.STOP_TIMEOUT,
                        None,
                    )
                    if response == "ACK STOP":
                        return True
                    self.log("warning", "Protocol v1 device did not acknowledge STOP")
                    return False
                self.ser.write(b"stop\n")
                response = self._wait_for_response_locked(
                    lambda line: line == "stop ok",
                    self.STOP_TIMEOUT,
                    None,
                )
            if response == "stop ok":
                return True
            self.log("warning", "Device did not acknowledge stop command")
            return False
        except Exception as exc:
            self.log("error", f"Error stopping device: {exc}")
            return False

    def _open_and_handshake(self, stop_event: threading.Event) -> bool:
        """Open a fresh transport and complete its handshake."""
        if stop_event.is_set() or serial is None:
            return False
        try:
            with self._io_lock:
                transport = serial.Serial(self.port, self.baud_rate, timeout=1)
                self.ser = transport
            if stop_event.wait(self.RESET_DELAY):
                return False
            if not self.start_device():
                self._close_transport()
                return False
            return True
        except Exception as exc:
            self.log("error", f"Failed to connect to StreamDeck: {exc}")
            self._close_transport()
            return False

    def _close_transport(self) -> None:
        with self._io_lock:
            transport, self.ser = self.ser, None
            if transport is not None:
                try:
                    transport.close()
                except Exception as exc:
                    self.log("warning", f"Error closing serial port: {exc}")

    def _ensure_workers_locked(self) -> None:
        if self._listener_thread is None or not self._listener_thread.is_alive():
            self._stop_listener.clear()
            self._listener_thread = threading.Thread(
                target=self._event_listener,
                name="streamdeck-serial-reader",
                daemon=True,
            )
            self._listener_thread.start()
        if self._command_thread is None or not self._command_thread.is_alive():
            self._stop_command.clear()
            self._command_thread = threading.Thread(
                target=self._command_processor,
                name="streamdeck-serial-writer",
                daemon=True,
            )
            self._command_thread.start()

    def _stop_workers_locked(self) -> bool:
        self._stop_listener.set()
        self._stop_command.set()
        self._wake_command_worker()
        listener_stopped = self._join_worker(self._listener_thread)
        command_stopped = self._join_worker(self._command_thread)
        if listener_stopped:
            self._listener_thread = None
        if command_stopped:
            self._command_thread = None
        return listener_stopped and command_stopped

    @staticmethod
    def _join_worker(worker: Optional[threading.Thread]) -> bool:
        if worker is None or not worker.is_alive():
            return True
        if worker is threading.current_thread():
            return False
        worker.join(timeout=4.0)
        return not worker.is_alive()

    def _event_listener(self) -> None:
        backoff = self.RECONNECT_INITIAL_DELAY
        while not self._stop_listener.is_set():
            if not self.is_connected():
                if self._stop_listener.wait(backoff):
                    break
                if self._open_and_handshake(self._stop_listener):
                    self._set_connected(True)
                    self.log("info", f"Reconnected to StreamDeck on {self.port}")
                    backoff = self.RECONNECT_INITIAL_DELAY
                else:
                    backoff = min(backoff * 2, self.RECONNECT_MAX_DELAY)
                continue

            try:
                try:
                    data = self._deferred_lines.get_nowait()
                except queue.Empty:
                    data = self._read_available_line()
                if data:
                    self.last_data = data
                    self._process_data(data)
                elif self._stop_listener.wait(self.READ_POLL_INTERVAL):
                    break
            except Exception as exc:
                if self._stop_listener.is_set():
                    break
                self.log("warning", f"Serial connection lost: {exc}")
                self._set_connected(False)
                self._close_transport()
                backoff = self.RECONNECT_INITIAL_DELAY

    def _read_available_line(self) -> Optional[str]:
        with self._io_lock:
            if self.ser is None:
                raise OSError("Serial transport is closed")
            if not self.ser.in_waiting:
                return None
            return self._decode_line(self.ser.readline())

    def _command_processor(self) -> None:
        pending: Optional[str] = None
        while not self._stop_command.is_set():
            if not self.is_connected():
                if self._stop_command.wait(self.COMMAND_POLL_INTERVAL):
                    break
                continue

            if pending is None:
                pending = self._next_command()
                if pending is None:
                    continue
            if self._send_command(pending):
                pending = None
            elif self._stop_command.wait(self.COMMAND_POLL_INTERVAL):
                break

        # Preserve an unsent command across automatic recovery, but not across an
        # explicit disconnect (which clears the queues after the join).
        if pending is not None and not self._stop_command.is_set():
            self._priority_command_queue.put(pending)

    def _next_command(self) -> Optional[str]:
        try:
            item = self._priority_command_queue.get_nowait()
        except queue.Empty:
            try:
                item = self._command_queue.get(timeout=self.COMMAND_POLL_INTERVAL)
            except queue.Empty:
                return None
        if item is self._QUEUE_STOP:
            return None
        return str(item)

    def _send_command(self, command: str) -> bool:
        if not self.is_connected():
            return False
        try:
            with self._io_lock:
                if self.ser is None:
                    return False
                self.ser.write(f"{command}\n".encode("utf-8"))
            self.log("debug", f"Sent command: {command}")
            return True
        except Exception as exc:
            self.log("error", f"Error sending command '{command}': {exc}")
            self._set_connected(False)
            self._close_transport()
            return False

    def send_command(self, command: str, priority: bool = False) -> None:
        """Queue a single-line command for reliable asynchronous delivery."""
        if not isinstance(command, str) or not command.strip():
            self.log("warning", "Ignored empty serial command")
            return
        if "\n" in command or "\r" in command:
            self.log("warning", "Ignored serial command containing a newline")
            return
        target = self._priority_command_queue if priority else self._command_queue
        target.put(command)

    def _wait_for_response_locked(
        self,
        predicate: Callable[[str], bool],
        timeout: float,
        stop_event: Optional[threading.Event],
    ) -> Optional[str]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if stop_event is not None and stop_event.is_set():
                return None
            if self.ser is None:
                return None
            if self.ser.in_waiting:
                line = self._decode_line(self.ser.readline())
                if not line:
                    continue
                if predicate(line):
                    return line
                # Preserve legitimate events received during negotiation.  Error
                # chatter from an old firmware is intentionally ignored.
                if not line.lower().startswith(("error", "unknown command")):
                    self._deferred_lines.put(line)
                continue
            remaining = max(0.0, deadline - time.monotonic())
            delay = min(self.READ_POLL_INTERVAL, remaining)
            if stop_event is not None:
                if stop_event.wait(delay):
                    return None
            else:
                time.sleep(delay)
        return None

    def _decode_line(self, raw: Any) -> Optional[str]:
        if isinstance(raw, bytes):
            text = raw.decode("utf-8", errors="replace")
        else:
            text = str(raw)
        text = text.replace("\x00", "").strip()
        if not text:
            return None
        if len(text) > self.MAX_LINE_LENGTH:
            self.log("warning", "Discarded oversized serial message")
            return None
        return text

    def _parse_ready(self, line: str) -> bool:
        parts = line.split()
        if len(parts) < 3 or parts[0] != "READY":
            return False
        try:
            protocol_version = int(parts[1])
        except ValueError:
            self.log("warning", f"Invalid device protocol version in: {line}")
            return False
        if protocol_version < 1:
            return False
        capabilities: Dict[str, str] = {}
        for token in parts[3:]:
            if "=" in token:
                key, value = token.split("=", 1)
                if key:
                    capabilities[key] = value
        self.protocol_version = protocol_version
        self.firmware_version = parts[2]
        self.capabilities = capabilities
        return True

    def _process_data(self, data: str) -> None:
        """Parse one complete device message without letting malformed data escape."""
        self.log("debug", f"Received: {data}")
        command, separator, payload = data.partition(" ")
        payload = payload.strip() if separator else ""

        no_arg_events = {
            "StartRecord": "record_start",
            "StopRecord": "record_stop",
            "StartStream": "stream_start",
            "StopStream": "stream_stop",
        }
        if command in no_arg_events and not payload:
            self._trigger_callback(no_arg_events[command])
            return
        if command == "ChangeScene" and payload:
            self._trigger_callback("scene_change", payload)
            return
        if command == "ExecuteScript" and payload:
            self._trigger_callback("execute_script", payload)
            return
        if command == "SetInputVolume":
            fields = payload.split()
            if len(fields) == 2:
                try:
                    value = int(fields[1])
                except ValueError:
                    pass
                else:
                    self._trigger_callback("volume_change", fields[0], value)
                    return

        # Unknown and malformed messages remain observable for diagnostics and
        # backwards-compatible custom firmware integrations.
        self._trigger_callback("data", data)

    def _trigger_callback(self, event_name: str, *args: Any) -> None:
        with self._callback_lock:
            callbacks = tuple(self.callbacks.get(event_name, ()))
        for callback in callbacks:
            try:
                callback(*args)
            except Exception as exc:
                self.log("error", f"Error in callback for {event_name}: {exc}")

    def register_callback(self, event_name: str, callback: Callable) -> None:
        """Register *callback* once for an event name."""
        if not callable(callback):
            raise TypeError("callback must be callable")
        with self._callback_lock:
            callbacks = self.callbacks.setdefault(event_name, [])
            if callback not in callbacks:
                callbacks.append(callback)

    def unregister_callback(self, event_name: str, callback: Callable) -> bool:
        with self._callback_lock:
            callbacks = self.callbacks.get(event_name)
            if callbacks and callback in callbacks:
                callbacks.remove(callback)
                if not callbacks:
                    self.callbacks.pop(event_name, None)
                return True
        return False

    def _set_connected(self, connected: bool) -> None:
        with self._state_lock:
            changed = self.connected != connected
            self.connected = connected
        if changed:
            self._trigger_callback("connection_state", connected)

    def set_led(self, led_index: int, state: bool) -> bool:
        if led_index not in (0, 1):
            return False
        if self.protocol_version and self.protocol_version >= 1:
            self.send_command(f"LED {led_index} {1 if state else 0}")
            return True
        led_type = "Stream" if led_index == 0 else "Record"
        state_str = "On" if state else "Off"
        self.send_command(f"{led_type}{state_str}Led")
        return True

    def enable_dumb_mode(self) -> None:
        self.send_command("DumbMode", priority=True)

    def disable_dumb_mode(self) -> None:
        self.send_command("NormalOperation", priority=True)

    def is_connected(self) -> bool:
        with self._state_lock:
            return self.connected

    def _wake_command_worker(self) -> None:
        self._priority_command_queue.put(self._QUEUE_STOP)

    @staticmethod
    def _clear_queue(target: "queue.Queue[object]") -> None:
        while True:
            try:
                target.get_nowait()
            except queue.Empty:
                return
