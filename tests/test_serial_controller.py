"""Hardware-independent tests for the serial controller."""

from __future__ import annotations

import queue
import threading
import time
import types
import unittest
from unittest.mock import patch

from src.hardware import serial_controller
from src.hardware.serial_controller import SerialController


def wait_until(predicate, timeout: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return bool(predicate())


class FakeSerial:
    def __init__(self, mode: str = "v1"):
        self.mode = mode
        self.incoming: "queue.Queue[bytes]" = queue.Queue()
        self.writes = []
        self.closed = False
        self.fail_reads = False
        self._lock = threading.Lock()

    @property
    def in_waiting(self):
        if self.fail_reads:
            raise OSError("cable removed")
        return self.incoming.qsize()

    def readline(self):
        try:
            return self.incoming.get_nowait()
        except queue.Empty:
            return b""

    def write(self, data: bytes):
        with self._lock:
            if self.closed:
                raise OSError("port closed")
            self.writes.append(data)
        if data == b"HELLO 1\n" and self.mode == "v1":
            self.push("READY 1 3.0.0 controls=B0-B3,P0-P3,G0-G3")
        elif data == b"START\n" and self.mode == "v1":
            self.push("ACK START")
        elif data == b"start\n" and self.mode == "legacy":
            self.push("start ok")
        elif data == b"STOP\n" and self.mode == "v1":
            self.push("ACK STOP")
        elif data == b"stop\n":
            self.push("stop ok")
        return len(data)

    def push(self, line):
        if isinstance(line, str):
            line = line.encode("utf-8")
        self.incoming.put(line + (b"" if line.endswith(b"\n") else b"\n"))

    def close(self):
        self.closed = True


class SerialFactory:
    def __init__(self, modes=("v1",)):
        self.modes = list(modes)
        self.instances = []

    def __call__(self, *_args, **_kwargs):
        index = min(len(self.instances), len(self.modes) - 1)
        instance = FakeSerial(self.modes[index])
        self.instances.append(instance)
        return instance


class SerialControllerTests(unittest.TestCase):
    def make_controller(self, factory: SerialFactory) -> SerialController:
        fake_module = types.SimpleNamespace(
            Serial=factory,
            tools=types.SimpleNamespace(
                list_ports=types.SimpleNamespace(comports=lambda: [])
            ),
        )
        patcher = patch.object(serial_controller, "serial", fake_module)
        patcher.start()
        self.addCleanup(patcher.stop)
        controller = SerialController(port="COM_TEST", baud_rate=115200)
        controller.RESET_DELAY = 0
        controller.HELLO_TIMEOUT = 0.03
        controller.LEGACY_START_TIMEOUT = 0.05
        controller.STOP_TIMEOUT = 0.05
        controller.READ_POLL_INTERVAL = 0.005
        controller.COMMAND_POLL_INTERVAL = 0.005
        controller.RECONNECT_INITIAL_DELAY = 0.01
        controller.RECONNECT_MAX_DELAY = 0.03
        self.addCleanup(controller.disconnect)
        return controller

    def test_v1_handshake_parses_metadata_and_workers_are_singletons(self):
        factory = SerialFactory()
        controller = self.make_controller(factory)
        states = []
        controller.register_callback("connection_state", states.append)

        self.assertTrue(controller.connect())
        reader = controller._listener_thread
        writer = controller._command_thread
        self.assertTrue(controller.connect())

        self.assertIs(controller._listener_thread, reader)
        self.assertIs(controller._command_thread, writer)
        self.assertEqual(controller.protocol_version, 1)
        self.assertEqual(controller.firmware_version, "3.0.0")
        self.assertEqual(
            controller.capabilities,
            {"controls": "B0-B3,P0-P3,G0-G3"},
        )
        self.assertIn(b"START\n", factory.instances[0].writes)
        self.assertEqual(states, [True])

        controller.disconnect()
        self.assertIn(b"STOP\n", factory.instances[0].writes)
        self.assertEqual(states, [True, False])
        self.assertFalse(reader.is_alive())
        self.assertFalse(writer.is_alive())

    def test_legacy_handshake_and_priority_queue(self):
        factory = SerialFactory(("legacy",))
        controller = self.make_controller(factory)
        controller.send_command("normal")
        controller.send_command("priority", priority=True)

        self.assertTrue(controller.connect())
        device = factory.instances[0]
        self.assertTrue(
            wait_until(
                lambda: b"normal\n" in device.writes
                and b"priority\n" in device.writes
            )
        )
        self.assertEqual(controller.protocol_version, 0)
        self.assertLess(
            device.writes.index(b"priority\n"),
            device.writes.index(b"normal\n"),
        )
        controller.set_led(0, True)
        self.assertTrue(wait_until(lambda: b"StreamOnLed\n" in device.writes))

    def test_v1_led_uses_versioned_command(self):
        factory = SerialFactory()
        controller = self.make_controller(factory)
        self.assertTrue(controller.connect())
        controller.set_led(1, False)
        self.assertTrue(wait_until(lambda: b"LED 1 0\n" in factory.instances[0].writes))

    def test_parser_contains_bad_input_and_preserves_unknown_messages(self):
        controller = self.make_controller(SerialFactory())
        volumes = []
        scenes = []
        raw = []
        controller.register_callback("volume_change", lambda *args: volumes.append(args))
        controller.register_callback("scene_change", scenes.append)
        controller.register_callback("data", raw.append)

        controller._process_data("SetInputVolume P0 not-a-number")
        controller._process_data("SetInputVolume P0 512")
        controller._process_data("ChangeScene Scene with spaces")
        controller._process_data("future protocol payload")

        self.assertEqual(volumes, [("P0", 512)])
        self.assertEqual(scenes, ["Scene with spaces"])
        self.assertEqual(
            raw,
            ["SetInputVolume P0 not-a-number", "future protocol payload"],
        )

    def test_reader_recovers_in_place_after_transport_failure(self):
        factory = SerialFactory(("v1", "v1"))
        controller = self.make_controller(factory)
        states = []
        controller.register_callback("connection_state", states.append)
        self.assertTrue(controller.connect())
        reader = controller._listener_thread

        factory.instances[0].fail_reads = True
        self.assertTrue(wait_until(lambda: len(factory.instances) >= 2))
        self.assertTrue(
            wait_until(
                lambda: controller.is_connected()
                and controller.ser is factory.instances[1]
            )
        )

        self.assertIs(controller._listener_thread, reader)
        self.assertTrue(reader.is_alive())
        self.assertEqual(states[:3], [True, False, True])

    def test_callbacks_can_be_changed_while_events_are_dispatched(self):
        controller = self.make_controller(SerialFactory())
        calls = []

        def callback():
            calls.append("called")
            controller.unregister_callback("record_start", callback)

        controller.register_callback("record_start", callback)
        controller.register_callback("record_start", callback)
        controller._process_data("StartRecord")
        controller._process_data("StartRecord")
        self.assertEqual(calls, ["called"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
