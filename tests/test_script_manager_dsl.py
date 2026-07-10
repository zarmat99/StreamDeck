import json
import threading

import pytest

from src.scripts.scripting import (
    ScriptManager,
    ScriptValidationError,
    parse_script,
)


class RecordingBackend:
    PAUSE = 0

    def __init__(self, fail_press=None, fail_key_down=None):
        self.events = []
        self.fail_press = fail_press
        self.fail_key_down = fail_key_down
        self.key_down_seen = threading.Event()
        self.key_up_seen = threading.Event()

    def press(self, key):
        self.events.append(("press", key))
        if key == self.fail_press:
            raise RuntimeError("press failed")

    def keyDown(self, key):
        self.events.append(("down", key))
        self.key_down_seen.set()
        if key == self.fail_key_down:
            raise RuntimeError("key down failed")

    def keyUp(self, key):
        self.events.append(("up", key))
        self.key_up_seen.set()

    def write(self, text):
        self.events.append(("write", text))

    def moveTo(self, x, y):
        self.events.append(("move", x, y))

    def click(self, *coordinates, button):
        self.events.append(("click", coordinates, button))


def test_parser_accepts_complete_declarative_dsl_and_canonicalizes():
    parsed = parse_script(
        """
        # a comment
        PRESS Enter
        combo ctrl$shift$s
        write Hello # this remains text
        delay 1.0
        move 10 20
        click right,30,40
        """
    )

    assert [command.to_source() for command in parsed] == [
        "press enter",
        "combo ctrl+shift+s",
        "write Hello # this remains text",
        "delay 1",
        "move 10,20",
        "click right,30,40",
    ]


@pytest.mark.parametrize(
    "code, message",
    [
        ("def run():", "unknown command"),
        ("combo ctrl", "at least two"),
        ("combo ctrl+ctrl", "duplicate"),
        ("delay nan", "between 0 and"),
        ("delay -1", "between 0 and"),
        ("move one,two", "integers"),
        ("click fourth", "left, right, or middle"),
        ("press two keys", "cannot contain whitespace"),
    ],
)
def test_parser_rejects_invalid_or_python_input_with_line_number(code, message):
    with pytest.raises(ScriptValidationError, match=message) as raised:
        parse_script(f"# first line\n{code}")
    assert raised.value.line_number == 2


def test_save_get_and_reload_script_code(tmp_path):
    path = tmp_path / "scripts.json"
    manager = ScriptManager(path, automation_backend=RecordingBackend())

    assert manager.save_script(
        "My automation", "# ignored\npress ENTER\ncombo ctrl$alt$t\nwrite hello"
    )
    assert manager.get_script_code("My automation") == (
        "press enter\ncombo ctrl+alt+t\nwrite hello"
    )
    assert manager.validate_script(manager.get_script_code("My automation"))

    reloaded = ScriptManager(path, automation_backend=RecordingBackend())
    assert reloaded.get_script("My automation") == [
        "press enter",
        "combo ctrl+alt+t",
        "write hello",
    ]


def test_legacy_string_and_object_formats_are_migrated_to_lists(tmp_path):
    path = tmp_path / "scripts.json"
    path.write_text(
        json.dumps(
            {
                "text": "press enter\nwrite hello",
                "object": {"commands": ["combo ctrl$k", "click left"]},
            }
        ),
        encoding="utf-8",
    )

    manager = ScriptManager(path, automation_backend=RecordingBackend())

    assert manager.scripts == {
        "text": ["press enter", "write hello"],
        "object": ["combo ctrl$k", "click left"],
    }
    assert json.loads(path.read_text(encoding="utf-8")) == manager.scripts


def test_scripts_recover_last_valid_backup(tmp_path):
    path = tmp_path / "scripts.json"
    manager = ScriptManager(path, automation_backend=RecordingBackend())
    manager.save_script("first", "press enter")
    manager.save_script("second", "press escape")
    path.write_text("not json", encoding="utf-8")

    recovered = ScriptManager(path, automation_backend=RecordingBackend())

    assert recovered.scripts == {"first": ["press enter"]}
    assert json.loads(path.read_text(encoding="utf-8")) == recovered.scripts


def test_combo_releases_every_key_when_key_down_fails(tmp_path):
    backend = RecordingBackend(fail_key_down="shift")
    manager = ScriptManager(tmp_path / "scripts.json", automation_backend=backend)

    assert manager.test_script("combo ctrl+shift+s") is False
    assert backend.events == [
        ("down", "ctrl"),
        ("down", "shift"),
        ("up", "shift"),
        ("up", "ctrl"),
    ]
    assert manager.running_scripts == set()


def test_explicitly_held_key_is_released_after_later_failure(tmp_path):
    backend = RecordingBackend(fail_press="escape")
    manager = ScriptManager(tmp_path / "scripts.json", automation_backend=backend)

    assert manager.test_script("hold ctrl\npress escape") is False
    assert backend.events[-1] == ("up", "ctrl")
    assert manager.running_scripts == set()


def test_async_duplicate_is_rejected_and_cancellation_releases_key(tmp_path):
    backend = RecordingBackend()
    manager = ScriptManager(tmp_path / "scripts.json", automation_backend=backend)
    manager.save_script("long", "hold ctrl\ndelay 30\nrelease ctrl")

    assert manager.execute_script("long", async_execution=True) is True
    assert backend.key_down_seen.wait(1)
    assert manager.execute_script("long", async_execution=True) is False
    assert manager.cancel_script("long") is True
    manager.cancel_all_scripts(timeout=1)
    assert backend.key_up_seen.wait(1)
    assert "long" not in manager.running_scripts
    assert backend.events[-1] == ("up", "ctrl")


def test_concurrent_saves_do_not_lose_other_scripts(tmp_path):
    manager = ScriptManager(
        tmp_path / "scripts.json", automation_backend=RecordingBackend()
    )
    results = []

    def save(index):
        results.append(manager.save_script(f"script-{index}", f"press f{index}"))

    threads = [threading.Thread(target=save, args=(index,)) for index in range(12)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert all(results)
    assert set(manager.scripts) == {f"script-{index}" for index in range(12)}
    assert json.loads((tmp_path / "scripts.json").read_text(encoding="utf-8")) == (
        manager.scripts
    )
