from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from types import SimpleNamespace
import threading

from src.app import StreamDeckApp


class RecordingLogger:
    def __init__(self):
        self.messages = []

    def debug(self, message):
        self.messages.append(("debug", message))

    def error(self, message):
        self.messages.append(("error", message))

    def info(self, message):
        self.messages.append(("info", message))


class FakePage:
    def __init__(self):
        self.shown = 0
        self.hidden = 0
        self.auto_connects = 0

    def show(self):
        self.shown += 1

    def hide(self):
        self.hidden += 1

    def start_auto_connect(self):
        self.auto_connects += 1


def bare_app():
    app = object.__new__(StreamDeckApp)
    app.logger = RecordingLogger()
    app._closing = False
    return app


def test_navigation_tracks_previous_page_and_rejects_unknown_page():
    app = bare_app()
    connection = FakePage()
    online = FakePage()
    app.pages = {"connection": connection, "online": online}
    app.current_page = None
    app.previous_page = None

    app.show_page("connection")
    app.show_page("online")
    app.go_back()
    app.show_page("missing")

    assert app.current_page == "connection"
    assert connection.shown == 2
    assert connection.hidden == 1
    assert online.shown == 1
    assert online.hidden == 1
    assert app.logger.messages[-1] == ("error", "Page 'missing' not found")


def test_background_results_and_errors_are_dispatched_on_ui_queue():
    app = bare_app()
    app._ui_queue = Queue()
    app._executor = ThreadPoolExecutor(max_workers=1)
    scheduled = []
    app._schedule_ui_queue = lambda: scheduled.append(True)
    successes = []
    errors = []
    try:
        success = app.submit_background(
            lambda: 42,
            successes.append,
            description="successful task",
        )
        assert success is not None
        success.result(timeout=2)
        app._drain_ui_queue()

        def fail():
            raise ValueError("broken")

        failure = app.submit_background(
            fail, on_error=errors.append, description="bad task"
        )
        assert failure is not None
        failure.result(timeout=2)
        app._drain_ui_queue()
    finally:
        app._executor.shutdown(wait=True)

    assert successes == [42]
    assert len(errors) == 1
    assert isinstance(errors[0], ValueError)
    assert scheduled == [True, True]
    assert ("error", "bad task failed: broken") in app.logger.messages


def test_dispatch_to_ui_runs_callback_only_when_application_is_open():
    app = bare_app()
    app._ui_queue = Queue()
    app._schedule_ui_queue = lambda: None
    calls = []

    app.dispatch_to_ui(lambda: calls.append("called"))
    app._drain_ui_queue()
    app._closing = True
    app.dispatch_to_ui(lambda: calls.append("late"))

    assert calls == ["called"]
    assert app._ui_queue.empty()


def test_auto_connect_respects_setting_and_shutdown_state():
    app = bare_app()
    page = FakePage()
    app.pages = {"connection": page}
    app.config = SimpleNamespace(settings={"connection": {"auto_connect": True}})

    app._auto_connect_if_enabled()
    app._closing = True
    app._auto_connect_if_enabled()

    assert page.auto_connects == 1


class FakeObs:
    def __init__(self, *, fail_volume=False):
        self.scenes = []
        self.volumes = []
        self.fail_volume = fail_volume

    def set_current_scene(self, scene):
        self.scenes.append(scene)

    def pot_to_db(self, value):
        return value / 1023, -12.5

    def set_volume(self, source, value):
        if self.fail_volume:
            raise RuntimeError("OBS unavailable")
        self.volumes.append((source, value))


def test_hardware_mapping_actions_and_volume_coalescing():
    app = bare_app()
    app.config = SimpleNamespace(
        settings={"mapping": {"B0": "Camera", "P0": "Mic", "G0": "Intro"}}
    )
    app.obs = FakeObs()
    script_calls = []
    app.script_manager = SimpleNamespace(
        execute_script=lambda name, async_execution: script_calls.append(
            (name, async_execution)
        )
    )
    actions = []
    app._submit_controller_action = lambda action, description: actions.append(
        (action, description)
    )

    app._handle_scene_change("B0")
    app._handle_script_execution("G0")
    for action, _description in actions:
        action()

    app._pot_lock = threading.Lock()
    app._pending_pot_values = {}
    app._active_pot_workers = set()
    app.submit_background = lambda task, **_kwargs: task()
    app._handle_volume_change("P0", 700)

    assert app.obs.scenes == ["Camera"]
    assert script_calls == [("Intro", True)]
    assert app.obs.volumes == [("Mic", -12.5)]
    assert app._pending_pot_values == {}
    assert app._active_pot_workers == set()


def test_volume_error_is_logged_and_worker_state_is_released():
    app = bare_app()
    app.config = SimpleNamespace(settings={"mapping": {"P1": "Desktop"}})
    app.obs = FakeObs(fail_volume=True)
    app._pot_lock = threading.Lock()
    app._pending_pot_values = {"P1": 100}
    app._active_pot_workers = {"P1"}

    app._drain_pot_values("P1")

    assert app._active_pot_workers == set()
    assert any(
        "Hardware volume update failed" in message for _, message in app.logger.messages
    )
