"""Thread-safe OBS WebSocket controller with bounded automatic recovery."""

from __future__ import annotations

import math
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple

try:  # Keep diagnostics/tests usable even when the optional OBS client is absent.
    from obswebsocket import events, obsws, requests
except ImportError:  # pragma: no cover - depends on the installation environment
    events = None  # type: ignore[assignment]
    obsws = None  # type: ignore[assignment]
    requests = None  # type: ignore[assignment]


class OBSController:
    """Control one OBS WebSocket endpoint.

    Every WebSocket operation is serialized by ``_io_lock`` because the client
    library does not promise concurrent ``call`` safety.  Exactly one health worker
    owns automatic reconnects.  ``connection_state`` callbacks receive a boolean on
    each effective state transition.

    Event callbacks can run on the OBS client's receive thread.  They are invoked
    outside controller locks, so they may safely call controller methods; GUI work
    still needs to be marshalled to the GUI thread by the consumer.
    """

    HEALTH_CHECK_INTERVAL = 2.0
    RECONNECT_INITIAL_DELAY = 0.5
    RECONNECT_MAX_DELAY = 8.0
    CLIENT_TIMEOUT = 3

    def __init__(
        self,
        host: str = "localhost",
        port: int = 4455,
        password: str = "",
        logger=None,
    ):
        self.host = host
        self.port = port
        self.password = password
        # obs-websocket-py ships without a complete type surface and tests inject
        # a protocol-compatible client double, so the transport remains dynamic.
        self.ws: Any = None
        self.connected = False
        self.logger = logger
        self.version: Optional[str] = None

        self.callbacks: Dict[str, List[Callable[..., Any]]] = {}
        self._callback_lock = threading.RLock()
        self._state_lock = threading.RLock()
        self._lifecycle_lock = threading.RLock()
        self._io_lock = threading.RLock()

        # _listener_thread and _stop_listener retain their historical names for
        # compatibility, but the worker is a health/recovery worker, not an event
        # reader (obs-websocket-py owns its own event receive thread).
        self._listener_thread: Optional[threading.Thread] = None
        self._stop_listener = threading.Event()
        self._reconnect_now = threading.Event()

    def log(self, level: str, message: str) -> None:
        if self.logger and hasattr(self.logger, level):
            getattr(self.logger, level)(message)

    def connect(self) -> bool:
        """Connect synchronously and start one health worker on success."""
        with self._lifecycle_lock:
            if self.is_connected():
                self._ensure_health_worker_locked()
                return True
            if obsws is None or requests is None or events is None:
                self.log("error", "Cannot connect: obs-websocket-py is not installed")
                return False

            self._stop_listener.clear()
            success = self._connect_transport()
            if success:
                self._ensure_health_worker_locked()
            elif self._listener_thread and self._listener_thread.is_alive():
                # A manual retry while the worker is recovering should wake its
                # interruptible backoff immediately, never create a second worker.
                self._reconnect_now.set()
            return success

    def disconnect(self) -> None:
        """Stop recovery, close the client, and wait for the health worker."""
        with self._lifecycle_lock:
            had_transport = self.ws is not None
            self._stop_listener.set()
            self._reconnect_now.set()
            self._disconnect_transport()
            worker = self._listener_thread
            if (
                worker
                and worker.is_alive()
                and worker is not threading.current_thread()
            ):
                worker.join(timeout=self.CLIENT_TIMEOUT + 1.0)
            if worker is None or not worker.is_alive():
                self._listener_thread = None
            elif worker is not threading.current_thread():
                self.log("warning", "OBS health worker did not stop before timeout")
            self._set_connected(False)
            if had_transport:
                self.log("info", "Disconnected from OBS WebSocket")

    def reconnect(self) -> bool:
        """Perform a clean explicit reconnect without recursive worker spawning."""
        self.disconnect()
        return self.connect()

    def _connect_transport(self) -> bool:
        """Create, verify, and publish a new client under the I/O lock."""
        if self._stop_listener.is_set() or obsws is None or requests is None:
            return False
        with self._io_lock:
            if self.is_connected() and self.ws is not None:
                return True
            self._disconnect_transport_locked()
            client = None
            try:
                client = obsws(
                    host=self.host,
                    port=self.port,
                    password=self.password,
                    timeout=self.CLIENT_TIMEOUT,
                )
                client.connect()
                version_response = client.call(requests.GetVersion())
                version = version_response.getObsVersion()
                self._register_events(client)
                if self._stop_listener.is_set():
                    client.disconnect()
                    return False
                self.ws = client
                self.version = version
            except Exception as exc:
                if client is not None:
                    try:
                        client.disconnect()
                    except Exception:
                        pass
                self.ws = None
                self.version = None
                self._set_connected(False)
                self.log("error", f"Failed to connect to OBS WebSocket: {exc}")
                return False

        self._set_connected(True)
        self.log("info", f"Connected to OBS WebSocket (OBS {self.version})")
        return True

    def _disconnect_transport(self) -> None:
        with self._io_lock:
            self._disconnect_transport_locked()

    def _disconnect_transport_locked(self) -> None:
        client, self.ws = self.ws, None
        if client is not None:
            try:
                client.disconnect()
            except Exception as exc:
                self.log("warning", f"Error disconnecting from OBS WebSocket: {exc}")
        self.version = None

    def _ensure_health_worker_locked(self) -> None:
        if self._listener_thread is not None and self._listener_thread.is_alive():
            return
        self._stop_listener.clear()
        self._reconnect_now.clear()
        self._listener_thread = threading.Thread(
            target=self._event_listener,
            name="streamdeck-obs-health",
            daemon=True,
        )
        self._listener_thread.start()

    def _register_events(self, client=None) -> None:
        target = client or self.ws
        if target is None or events is None:
            return
        target.register(self._on_stream_status_change, events.StreamStateChanged)
        target.register(self._on_record_status_change, events.RecordStateChanged)
        target.register(self._on_scene_change, events.CurrentProgramSceneChanged)
        target.register(self._on_input_volume_change, events.InputVolumeChanged)
        # Older OBS client packages may not expose InputMuteStateChanged.
        mute_event = getattr(events, "InputMuteStateChanged", None)
        if mute_event is not None:
            target.register(self._on_input_mute_change, mute_event)

    def _event_listener(self) -> None:
        """Health/recovery loop; this is the sole owner of automatic reconnects."""
        backoff = self.RECONNECT_INITIAL_DELAY
        while not self._stop_listener.is_set():
            if self.is_connected():
                if self._wait_interruptibly(self.HEALTH_CHECK_INTERVAL):
                    break
                try:
                    self._call_raw(requests.GetVersion())
                    backoff = self.RECONNECT_INITIAL_DELAY
                    continue
                except Exception as exc:
                    if self._stop_listener.is_set():
                        break
                    self.log("warning", f"OBS WebSocket connection lost: {exc}")
                    self._mark_connection_lost()

            if self._wait_interruptibly(backoff):
                break
            if self._connect_transport():
                backoff = self.RECONNECT_INITIAL_DELAY
                self.log("info", "OBS WebSocket connection recovered")
            else:
                backoff = min(backoff * 2, self.RECONNECT_MAX_DELAY)

    def _wait_interruptibly(self, timeout: float) -> bool:
        """Wait for stop or an explicit reconnect wake-up.

        Returns True only when shutdown was requested.
        """
        self._reconnect_now.wait(timeout)
        self._reconnect_now.clear()
        return self._stop_listener.is_set()

    def _mark_connection_lost(self) -> None:
        self._set_connected(False)
        self._disconnect_transport()
        self._reconnect_now.set()

    def _call_raw(self, request: Any) -> Any:
        """Execute one request while serializing all client I/O."""
        with self._io_lock:
            client = self.ws
            if client is None or not self.is_connected():
                raise ConnectionError("Not connected to OBS")
            return client.call(request)

    def _request(
        self,
        request: Any,
        operation: str,
        default: Any,
        transform: Callable[[Any], Any] = lambda response: response,
    ) -> Any:
        if not self.is_connected():
            return default
        try:
            return transform(self._call_raw(request))
        except Exception as exc:
            self.log("error", f"{operation}: {exc}")
            return default

    def _on_stream_status_change(self, message: Any) -> None:
        streaming = bool(message.getOutputActive())
        self.log("info", f"Streaming {'started' if streaming else 'stopped'}")
        self._trigger_callback("streaming_state", streaming)

    def _on_record_status_change(self, message: Any) -> None:
        recording = bool(message.getOutputActive())
        self.log("info", f"Recording {'started' if recording else 'stopped'}")
        self._trigger_callback("recording_state", recording)

    def _on_scene_change(self, message: Any) -> None:
        scene_name = message.getSceneName()
        self.log("info", f"Scene changed to '{scene_name}'")
        self._trigger_callback("scene_change", scene_name)

    def _on_input_volume_change(self, message: Any) -> None:
        input_name = message.getInputName()
        volume_db = message.getInputVolumeDb()
        self.log("debug", f"Volume changed for '{input_name}': {volume_db} dB")
        self._trigger_callback("volume_change", input_name, volume_db)

    def _on_input_mute_change(self, message: Any) -> None:
        input_name = message.getInputName()
        muted = bool(message.getInputMuted())
        self.log("debug", f"Mute changed for '{input_name}': {muted}")
        self._trigger_callback("mute_change", input_name, muted)

    def _trigger_callback(self, event_name: str, *args: Any) -> None:
        with self._callback_lock:
            callbacks = tuple(self.callbacks.get(event_name, ()))
        for callback in callbacks:
            try:
                callback(*args)
            except Exception as exc:
                self.log("error", f"Error in callback for {event_name}: {exc}")

    def register_callback(self, event_name: str, callback: Callable) -> None:
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

    def start_streaming(self) -> bool:
        if requests is None:
            return False
        response = self._request(
            requests.StartStream(), "Failed to start streaming", None
        )
        if response is None:
            return False
        self.log("info", "Streaming start requested")
        return True

    def stop_streaming(self) -> bool:
        if requests is None:
            return False
        response = self._request(
            requests.StopStream(), "Failed to stop streaming", None
        )
        if response is None:
            return False
        self.log("info", "Streaming stop requested")
        return True

    def start_recording(self) -> bool:
        if requests is None:
            return False
        response = self._request(
            requests.StartRecord(), "Failed to start recording", None
        )
        if response is None:
            return False
        self.log("info", "Recording start requested")
        return True

    def stop_recording(self) -> bool:
        if requests is None:
            return False
        response = self._request(
            requests.StopRecord(), "Failed to stop recording", None
        )
        if response is None:
            return False
        self.log("info", "Recording stop requested")
        return True

    def get_streaming_status(self) -> bool:
        if requests is None:
            return False
        return bool(
            self._request(
                requests.GetStreamStatus(),
                "Failed to get streaming status",
                False,
                lambda response: response.getOutputActive(),
            )
        )

    def get_recording_status(self) -> bool:
        if requests is None:
            return False
        return bool(
            self._request(
                requests.GetRecordStatus(),
                "Failed to get recording status",
                False,
                lambda response: response.getOutputActive(),
            )
        )

    def get_scene_list(self) -> List[str]:
        if requests is None:
            return []
        return self._request(
            requests.GetSceneList(),
            "Failed to get scene list",
            [],
            lambda response: [
                scene["sceneName"]
                for scene in response.getScenes()
                if "sceneName" in scene
            ],
        )

    def get_current_scene(self) -> Optional[str]:
        if requests is None:
            return None
        return self._request(
            requests.GetCurrentProgramScene(),
            "Failed to get current scene",
            None,
            lambda response: response.getCurrentProgramSceneName(),
        )

    def set_current_scene(self, scene_name: str) -> bool:
        if requests is None:
            return False
        response = self._request(
            requests.SetCurrentProgramScene(sceneName=scene_name),
            f"Failed to set scene '{scene_name}'",
            None,
        )
        if response is None:
            return False
        self.log("info", f"Scene change requested: '{scene_name}'")
        return True

    def get_volume_sources(self) -> List[str]:
        """Return all OBS input names, independent of platform/input kind.

        OBS does not expose a portable audio-capability flag in ``GetInputList``.
        Actual volume calls remain the source of truth and return ``None``/``False``
        for inputs that do not implement audio controls.
        """
        if requests is None:
            return []
        return self._request(
            requests.GetInputList(),
            "Failed to get volume sources",
            [],
            lambda response: list(
                dict.fromkeys(
                    item["inputName"]
                    for item in response.getInputs()
                    if item.get("inputName")
                )
            ),
        )

    def get_volume(self, source_name: str) -> Optional[float]:
        if requests is None:
            return None
        return self._request(
            requests.GetInputVolume(inputName=source_name),
            f"Failed to get volume for '{source_name}'",
            None,
            lambda response: response.getInputVolumeDb(),
        )

    def set_volume(self, source_name: str, volume_db: float) -> bool:
        if requests is None:
            return False
        response = self._request(
            requests.SetInputVolume(
                inputName=source_name, inputVolumeDb=float(volume_db)
            ),
            f"Failed to set volume for '{source_name}'",
            None,
        )
        if response is None:
            return False
        self.log("debug", f"Volume set for '{source_name}': {volume_db} dB")
        return True

    def get_mute(self, source_name: str) -> Optional[bool]:
        """Return the OBS mute state for an input."""
        if requests is None:
            return None
        return self._request(
            requests.GetInputMute(inputName=source_name),
            f"Failed to get mute state for '{source_name}'",
            None,
            lambda response: bool(response.getInputMuted()),
        )

    def set_mute(self, source_name: str, muted: bool) -> bool:
        """Set an input's OBS mute state without destroying its prior volume."""
        if requests is None:
            return False
        response = self._request(
            requests.SetInputMute(inputName=source_name, inputMuted=bool(muted)),
            f"Failed to set mute state for '{source_name}'",
            None,
        )
        if response is None:
            return False
        self.log("debug", f"Mute set for '{source_name}': {bool(muted)}")
        return True

    def pot_to_db(self, pot_value: int) -> Tuple[int, float]:
        min_pot = 94
        max_pot = 1022
        min_db = -100
        max_db = 0
        if pot_value <= min_pot:
            return min_pot, min_db
        if pot_value >= max_pot:
            return max_pot, max_db
        db = (
            math.log10(pot_value - min_pot + 1) / math.log10(max_pot - min_pot + 1)
        ) * (max_db - min_db) + min_db
        return pot_value, db

    def is_connected(self) -> bool:
        with self._state_lock:
            return self.connected
