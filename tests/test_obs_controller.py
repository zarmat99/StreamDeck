"""OBS-controller tests using a fully in-memory fake WebSocket backend."""

from __future__ import annotations

import threading
import time
import types
import unittest
from unittest.mock import patch

from src.obs import obs_controller
from src.obs.obs_controller import OBSController


def wait_until(predicate, timeout: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return bool(predicate())


class FakeRequest:
    def __init__(self, name, **kwargs):
        self.name = name
        self.kwargs = kwargs


class FakeRequests:
    @staticmethod
    def _make(name):
        return lambda **kwargs: FakeRequest(name, **kwargs)


for _request_name in (
    "GetVersion",
    "StartStream",
    "StopStream",
    "StartRecord",
    "StopRecord",
    "GetStreamStatus",
    "GetRecordStatus",
    "GetSceneList",
    "GetCurrentProgramScene",
    "SetCurrentProgramScene",
    "GetInputList",
    "GetInputVolume",
    "SetInputVolume",
    "GetInputMute",
    "SetInputMute",
):
    setattr(
        FakeRequests, _request_name, staticmethod(FakeRequests._make(_request_name))
    )


class FakeEvents:
    StreamStateChanged = type("StreamStateChanged", (), {})
    RecordStateChanged = type("RecordStateChanged", (), {})
    CurrentProgramSceneChanged = type("CurrentProgramSceneChanged", (), {})
    InputVolumeChanged = type("InputVolumeChanged", (), {})
    InputMuteStateChanged = type("InputMuteStateChanged", (), {})


class FakeResponse:
    def __init__(self, **values):
        self.values = values

    def getObsVersion(self):
        return self.values.get("version", "31.0.0")

    def getOutputActive(self):
        return self.values.get("active", False)

    def getScenes(self):
        return self.values.get("scenes", [])

    def getCurrentProgramSceneName(self):
        return self.values.get("scene", "Main")

    def getInputs(self):
        return self.values.get("inputs", [])

    def getInputVolumeDb(self):
        return self.values.get("volume", -12.5)

    def getInputMuted(self):
        return self.values.get("muted", False)


class FakeOBSClient:
    def __init__(self, fail_version_after=None, call_delay=0.0):
        self.fail_version_after = fail_version_after
        self.call_delay = call_delay
        self.connected = False
        self.version_calls = 0
        self.calls = []
        self.registrations = []
        self.max_active_calls = 0
        self._active_calls = 0
        self._counter_lock = threading.Lock()

    def connect(self):
        self.connected = True

    def disconnect(self):
        self.connected = False

    def register(self, callback, event):
        self.registrations.append((callback, event))

    def call(self, request):
        with self._counter_lock:
            self._active_calls += 1
            self.max_active_calls = max(self.max_active_calls, self._active_calls)
        try:
            if self.call_delay:
                time.sleep(self.call_delay)
            if not self.connected:
                raise ConnectionError("fake client disconnected")
            self.calls.append(request)
            if request.name == "GetVersion":
                self.version_calls += 1
                if (
                    self.fail_version_after is not None
                    and self.version_calls > self.fail_version_after
                ):
                    raise ConnectionError("fake connection lost")
                return FakeResponse(version="31.0.0")
            if request.name in ("GetStreamStatus", "GetRecordStatus"):
                return FakeResponse(active=True)
            if request.name == "GetSceneList":
                return FakeResponse(
                    scenes=[{"sceneName": "Main"}, {"sceneName": "BRB"}]
                )
            if request.name == "GetCurrentProgramScene":
                return FakeResponse(scene="Main")
            if request.name == "GetInputList":
                return FakeResponse(
                    inputs=[
                        {"inputName": "Desktop", "inputKind": "wasapi_output_capture"},
                        {"inputName": "Camera", "inputKind": "dshow_input"},
                        {"inputName": "Browser", "inputKind": "browser_source"},
                        {"inputName": "Camera", "inputKind": "dshow_input"},
                    ]
                )
            if request.name == "GetInputVolume":
                return FakeResponse(volume=-7.0)
            if request.name == "GetInputMute":
                return FakeResponse(muted=True)
            return FakeResponse()
        finally:
            with self._counter_lock:
                self._active_calls -= 1


class FakeOBSFactory:
    def __init__(self, configurations=None):
        self.configurations = configurations or [{}]
        self.instances = []

    def __call__(self, **_kwargs):
        index = min(len(self.instances), len(self.configurations) - 1)
        client = FakeOBSClient(**self.configurations[index])
        self.instances.append(client)
        return client


class OBSControllerTests(unittest.TestCase):
    def make_controller(self, factory: FakeOBSFactory) -> OBSController:
        patchers = (
            patch.object(obs_controller, "obsws", factory),
            patch.object(obs_controller, "requests", FakeRequests),
            patch.object(obs_controller, "events", FakeEvents),
        )
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        controller = OBSController(password="secret")
        controller.HEALTH_CHECK_INTERVAL = 0.02
        controller.RECONNECT_INITIAL_DELAY = 0.01
        controller.RECONNECT_MAX_DELAY = 0.03
        self.addCleanup(controller.disconnect)
        return controller

    def test_connect_is_idempotent_and_disconnect_stops_health_worker(self):
        factory = FakeOBSFactory()
        controller = self.make_controller(factory)
        states = []
        controller.register_callback("connection_state", states.append)

        self.assertTrue(controller.connect())
        worker = controller._listener_thread
        self.assertTrue(controller.connect())
        self.assertIs(controller._listener_thread, worker)
        self.assertEqual(len(factory.instances), 1)
        self.assertEqual(len(factory.instances[0].registrations), 5)
        self.assertEqual(states, [True])

        controller.disconnect()
        self.assertFalse(worker.is_alive())
        self.assertEqual(states, [True, False])

    def test_health_worker_recovers_without_replacing_itself(self):
        factory = FakeOBSFactory(
            [{"fail_version_after": 1}, {"fail_version_after": None}]
        )
        controller = self.make_controller(factory)
        states = []
        controller.register_callback("connection_state", states.append)
        self.assertTrue(controller.connect())
        worker = controller._listener_thread

        self.assertTrue(wait_until(lambda: len(factory.instances) >= 2))
        self.assertTrue(
            wait_until(
                lambda: (
                    controller.is_connected() and controller.ws is factory.instances[1]
                )
            )
        )
        self.assertIs(controller._listener_thread, worker)
        self.assertTrue(worker.is_alive())
        self.assertEqual(states[:3], [True, False, True])

    def test_all_calls_are_serialized_across_client_threads(self):
        factory = FakeOBSFactory([{"call_delay": 0.015}])
        controller = self.make_controller(factory)
        controller.HEALTH_CHECK_INTERVAL = 10
        self.assertTrue(controller.connect())
        client = factory.instances[0]

        results = []
        threads = [
            threading.Thread(
                target=lambda value=index: results.append(
                    controller.set_volume("Desktop", -float(value))
                )
            )
            for index in range(8)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=1)

        self.assertEqual(results, [True] * 8)
        self.assertEqual(client.max_active_calls, 1)

    def test_cross_platform_inputs_and_mute_api(self):
        controller = self.make_controller(FakeOBSFactory())
        self.assertTrue(controller.connect())

        self.assertEqual(
            controller.get_volume_sources(),
            ["Desktop", "Camera", "Browser"],
        )
        self.assertEqual(controller.get_volume("Camera"), -7.0)
        self.assertTrue(controller.get_mute("Camera"))
        self.assertTrue(controller.set_mute("Camera", False))
        last_request = controller.ws.calls[-1]
        self.assertEqual(last_request.name, "SetInputMute")
        self.assertEqual(
            last_request.kwargs,
            {"inputName": "Camera", "inputMuted": False},
        )

    def test_callback_registry_is_reentrant_and_deduplicated(self):
        controller = self.make_controller(FakeOBSFactory())
        calls = []

        def callback(state):
            calls.append(state)
            controller.unregister_callback("streaming_state", callback)

        controller.register_callback("streaming_state", callback)
        controller.register_callback("streaming_state", callback)
        message = types.SimpleNamespace(getOutputActive=lambda: True)
        controller._on_stream_status_change(message)
        controller._on_stream_status_change(message)
        self.assertEqual(calls, [True])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
