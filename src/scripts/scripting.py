"""Declarative, validated desktop automation scripts.

The on-disk representation remains compatible with previous releases: a JSON
object maps script names to lists of command strings.  The editor-facing API
uses the same commands as a small textual DSL.  No Python source is evaluated.
"""

from __future__ import annotations

from dataclasses import dataclass
import itertools
import math
import os
from pathlib import Path
import re
import threading
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

try:
    import pyautogui as _pyautogui
except Exception:  # Allows validation/configuration on headless hosts.
    _pyautogui = None

try:
    from utils.config_manager import (
        atomic_write_json,
        default_config_dir,
        read_json_with_backup,
    )
except ImportError:  # Package-style imports used by tests and tooling.
    from ..utils.config_manager import (
        atomic_write_json,
        default_config_dir,
        read_json_with_backup,
    )


COMMAND_LIST = ["press", "hold", "release", "combo", "write", "delay", "move", "click"]
MAX_COMMANDS = 1_000
MAX_DELAY_SECONDS = 3_600.0
MAX_WRITE_LENGTH = 10_000
_VALID_BUTTONS = {"left", "right", "middle"}
_KEY_PATTERN = re.compile(r"^[^\s+$]+$")
_AUTOMATION_LOCK = threading.RLock()


class ScriptValidationError(ValueError):
    """Raised when a line in the declarative script is invalid."""

    def __init__(self, line_number: int, message: str, source: str = "") -> None:
        self.line_number = line_number
        self.message = message
        self.source = source
        prefix = f"Line {line_number}: " if line_number else ""
        super().__init__(prefix + message)


@dataclass(frozen=True)
class ScriptCommand:
    """One parsed DSL command."""

    operation: str
    arguments: Tuple[Any, ...]
    line_number: int
    source: str

    def to_source(self) -> str:
        if self.operation in {"press", "hold", "release"}:
            return f"{self.operation} {self.arguments[0]}"
        if self.operation == "combo":
            return f"combo {'+'.join(self.arguments)}"
        if self.operation == "write":
            return f"write {self.arguments[0]}"
        if self.operation == "delay":
            return f"delay {self.arguments[0]:.15g}"
        if self.operation == "move":
            return f"move {self.arguments[0]},{self.arguments[1]}"
        if self.operation == "click":
            if len(self.arguments) == 1:
                return f"click {self.arguments[0]}"
            return f"click {self.arguments[0]},{self.arguments[1]},{self.arguments[2]}"
        raise AssertionError(f"Unsupported parsed operation: {self.operation}")


def _validate_key(value: str, line_number: int, source: str) -> str:
    key = value.strip().lower()
    if not key or len(key) > 64 or not _KEY_PATTERN.fullmatch(key):
        raise ScriptValidationError(
            line_number, "key names cannot contain whitespace, '+' or '$'", source
        )
    return key


def _parse_coordinates(
    value: str, count: int, line_number: int, source: str
) -> Tuple[int, ...]:
    fields = [item for item in re.split(r"[\s,]+", value.strip()) if item]
    if len(fields) != count:
        raise ScriptValidationError(
            line_number, f"expected {count} integer coordinate values", source
        )
    try:
        return tuple(int(item) for item in fields)
    except ValueError as error:
        raise ScriptValidationError(
            line_number, "coordinates must be integers", source
        ) from error


def parse_script(script_code: str) -> List[ScriptCommand]:
    """Parse the declarative DSL and return typed commands.

    Blank lines and lines whose first non-space character is ``#`` are ignored.
    Invalid input raises :class:`ScriptValidationError` with a line number.
    """

    if not isinstance(script_code, str):
        raise ScriptValidationError(0, "script code must be text")

    parsed: List[ScriptCommand] = []
    for line_number, source in enumerate(script_code.splitlines(), start=1):
        stripped = source.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if len(parsed) >= MAX_COMMANDS:
            raise ScriptValidationError(
                line_number, f"scripts may contain at most {MAX_COMMANDS} commands", source
            )

        fields = stripped.split(None, 1)
        operation = fields[0].lower()
        argument = fields[1].strip() if len(fields) == 2 else ""
        if operation not in COMMAND_LIST:
            raise ScriptValidationError(
                line_number,
                f"unknown command '{operation}'; expected one of {', '.join(COMMAND_LIST)}",
                source,
            )

        if operation in {"press", "hold", "release"}:
            if not argument:
                raise ScriptValidationError(line_number, "missing key name", source)
            key = _validate_key(argument, line_number, source)
            parsed.append(ScriptCommand(operation, (key,), line_number, source))
            continue

        if operation == "combo":
            if "$" in argument:
                raw_keys = argument.split("$")
            elif "+" in argument:
                raw_keys = argument.split("+")
            else:
                raw_keys = argument.split()
            if not raw_keys or any(not key.strip() for key in raw_keys):
                raise ScriptValidationError(
                    line_number, "combo contains an empty key", source
                )
            keys = tuple(
                _validate_key(key, line_number, source) for key in raw_keys
            )
            if len(keys) < 2:
                raise ScriptValidationError(
                    line_number, "combo requires at least two keys", source
                )
            if len(set(keys)) != len(keys):
                raise ScriptValidationError(
                    line_number, "combo cannot contain duplicate keys", source
                )
            parsed.append(ScriptCommand(operation, keys, line_number, source))
            continue

        if operation == "write":
            if not argument:
                raise ScriptValidationError(line_number, "write requires text", source)
            if len(argument) > MAX_WRITE_LENGTH:
                raise ScriptValidationError(
                    line_number,
                    f"write text may contain at most {MAX_WRITE_LENGTH} characters",
                    source,
                )
            parsed.append(ScriptCommand(operation, (argument,), line_number, source))
            continue

        if operation == "delay":
            try:
                seconds = float(argument)
            except ValueError as error:
                raise ScriptValidationError(
                    line_number, "delay requires a number of seconds", source
                ) from error
            if not math.isfinite(seconds) or not 0 <= seconds <= MAX_DELAY_SECONDS:
                raise ScriptValidationError(
                    line_number,
                    f"delay must be between 0 and {MAX_DELAY_SECONDS:g} seconds",
                    source,
                )
            parsed.append(ScriptCommand(operation, (seconds,), line_number, source))
            continue

        if operation == "move":
            coordinates = _parse_coordinates(argument, 2, line_number, source)
            parsed.append(ScriptCommand(operation, coordinates, line_number, source))
            continue

        if operation == "click":
            fields = [item for item in re.split(r"[\s,]+", argument) if item]
            if len(fields) not in (1, 3):
                raise ScriptValidationError(
                    line_number, "click expects BUTTON or BUTTON,X,Y", source
                )
            button = fields[0].lower() if fields else ""
            if button not in _VALID_BUTTONS:
                raise ScriptValidationError(
                    line_number, "click button must be left, right, or middle", source
                )
            if len(fields) == 1:
                parsed.append(ScriptCommand(operation, (button,), line_number, source))
            else:
                coordinates = _parse_coordinates(
                    ",".join(fields[1:]), 2, line_number, source
                )
                parsed.append(
                    ScriptCommand(operation, (button,) + coordinates, line_number, source)
                )

    return parsed


def _commands_to_code(commands: Union[str, Sequence[str]]) -> str:
    if isinstance(commands, str):
        return commands
    if not isinstance(commands, Sequence) or not all(
        isinstance(command, str) for command in commands
    ):
        raise ScriptValidationError(0, "commands must be text or a list of text lines")
    return "\n".join(commands)


def _normalize_scripts(payload: Any) -> Tuple[Dict[str, List[str]], bool]:
    """Normalize historical script representations without evaluating them."""

    if not isinstance(payload, Mapping):
        return {}, payload not in (None, {})
    normalized: Dict[str, List[str]] = {}
    changed = False
    for raw_name, raw_script in payload.items():
        if not isinstance(raw_name, str) or not raw_name.strip():
            changed = True
            continue
        name = raw_name.strip()
        if name != raw_name:
            changed = True

        if isinstance(raw_script, str):
            lines = raw_script.splitlines()
            changed = True
        elif isinstance(raw_script, list) and all(
            isinstance(line, str) for line in raw_script
        ):
            lines = list(raw_script)
        elif isinstance(raw_script, Mapping):
            candidate = raw_script.get("commands", raw_script.get("code"))
            if isinstance(candidate, str):
                lines = candidate.splitlines()
            elif isinstance(candidate, list) and all(
                isinstance(line, str) for line in candidate
            ):
                lines = list(candidate)
            else:
                changed = True
                continue
            changed = True
        else:
            changed = True
            continue
        normalized[name] = lines
    return normalized, changed


class ScriptManager:
    """Thread-safe repository and executor for declarative automations."""

    def __init__(
        self,
        scripts_path: Optional[Union[str, os.PathLike[str]]] = None,
        logger: Any = None,
        automation_backend: Any = None,
    ) -> None:
        self.scripts_path = str(
            Path(scripts_path) if scripts_path is not None else Path(default_config_dir()) / "scripts.json"
        )
        self.scripts: Dict[str, List[str]] = {}
        self.logger = logger
        self.running_scripts: set[str] = set()
        self._cancel_events: Dict[str, threading.Event] = {}
        self._threads: Dict[str, threading.Thread] = {}
        self._lock = threading.RLock()
        self._test_ids = itertools.count(1)
        self._backend = automation_backend if automation_backend is not None else _pyautogui
        if self._backend is not None and hasattr(self._backend, "PAUSE"):
            self._backend.PAUSE = 0.01

        Path(self.scripts_path).parent.mkdir(parents=True, exist_ok=True)
        self.load_scripts()

    def log(self, level: str, message: str) -> None:
        if self.logger and hasattr(self.logger, level):
            getattr(self.logger, level)(message)

    def _save_snapshot(self, snapshot: Mapping[str, Sequence[str]]) -> None:
        payload = {name: list(commands) for name, commands in snapshot.items()}
        atomic_write_json(self.scripts_path, payload)

    def save_scripts(self) -> bool:
        """Atomically persist a consistent snapshot of all scripts."""

        with self._lock:
            snapshot = {name: list(commands) for name, commands in self.scripts.items()}
            try:
                self._save_snapshot(snapshot)
                self.log("debug", f"Scripts saved to {self.scripts_path}")
                return True
            except (OSError, TypeError, ValueError) as error:
                self.log("error", f"Error saving scripts: {error}")
                return False

    def load_scripts(self) -> Dict[str, List[str]]:
        """Load scripts, recovering the last valid atomic backup if needed."""

        with self._lock:
            path = Path(self.scripts_path)
            raw, recovered = read_json_with_backup(path)
            normalized, changed = _normalize_scripts(raw)
            self.scripts = normalized
            if recovered or changed or raw is None or not path.exists():
                try:
                    self._save_snapshot(normalized)
                except (OSError, TypeError, ValueError) as error:
                    self.log("error", f"Error repairing scripts file: {error}")
            self.log("debug", f"Scripts loaded from {self.scripts_path}")
            return {name: list(commands) for name, commands in self.scripts.items()}

    def _commit_change(self, new_scripts: Dict[str, List[str]]) -> bool:
        try:
            self._save_snapshot(new_scripts)
        except (OSError, TypeError, ValueError) as error:
            self.log("error", f"Error saving scripts: {error}")
            return False
        self.scripts = new_scripts
        return True

    def create_script(self, name: str, commands: Optional[List[str]] = None) -> bool:
        """Create or replace a script after validating all commands."""

        if not isinstance(name, str) or not name.strip():
            self.log("error", "Cannot create script without a name")
            return False
        name = name.strip()
        commands = list(commands or [])
        if commands:
            try:
                parsed = parse_script(_commands_to_code(commands))
            except ScriptValidationError as error:
                self.log("error", f"Cannot create invalid script '{name}': {error}")
                return False
            commands = [command.to_source() for command in parsed]
        with self._lock:
            updated = {key: list(value) for key, value in self.scripts.items()}
            updated[name] = commands
            saved = self._commit_change(updated)
        if saved:
            self.log("info", f"Script '{name}' created with {len(commands)} commands")
        return saved

    def save_script(self, name: str, script_code: str) -> bool:
        """Validate DSL text and atomically create or replace one script."""

        if not isinstance(name, str) or not name.strip():
            raise ScriptValidationError(0, "script name cannot be empty")
        parsed = parse_script(script_code)
        if not parsed:
            raise ScriptValidationError(0, "script must contain at least one command")
        commands = [command.to_source() for command in parsed]
        clean_name = name.strip()
        with self._lock:
            updated = {key: list(value) for key, value in self.scripts.items()}
            updated[clean_name] = commands
            saved = self._commit_change(updated)
        if saved:
            self.log("info", f"Script '{clean_name}' saved")
        return saved

    def delete_script(self, name: str) -> bool:
        """Delete a script and request safe cancellation if it is running."""

        self.cancel_script(name)
        with self._lock:
            if name not in self.scripts:
                self.log("warning", f"Script '{name}' not found, cannot delete")
                return False
            updated = {key: list(value) for key, value in self.scripts.items()}
            del updated[name]
            saved = self._commit_change(updated)
        if saved:
            self.log("info", f"Script '{name}' deleted")
        return saved

    def get_script(self, name: str) -> Optional[List[str]]:
        with self._lock:
            commands = self.scripts.get(name)
            if commands is not None:
                return list(commands)
        self.log("warning", f"Script '{name}' not found")
        return None

    def get_script_code(self, name: str) -> str:
        """Return editor-ready DSL text, or an empty string for a missing script."""

        commands = self.get_script(name)
        return "\n".join(commands) if commands is not None else ""

    def validate_script(self, script_code: str) -> bool:
        """Return ``True`` for valid, non-empty DSL; otherwise raise."""

        if not parse_script(script_code):
            raise ScriptValidationError(0, "script must contain at least one command")
        return True

    def _reserve(self, script_name: str) -> Optional[threading.Event]:
        with self._lock:
            if script_name in self.running_scripts:
                return None
            event = threading.Event()
            self.running_scripts.add(script_name)
            self._cancel_events[script_name] = event
            return event

    def execute_script(self, script_name: str, async_execution: bool = False) -> bool:
        """Execute a stored script once, optionally on a daemon worker."""

        commands = self.get_script(script_name)
        if not commands:
            return False
        try:
            parsed = parse_script(_commands_to_code(commands))
        except ScriptValidationError as error:
            self.log("error", f"Invalid script '{script_name}': {error}")
            return False
        cancel_event = self._reserve(script_name)
        if cancel_event is None:
            self.log("warning", f"Script '{script_name}' is already running")
            return False

        if async_execution:
            thread = threading.Thread(
                target=self._run_reserved,
                args=(script_name, parsed, cancel_event),
                daemon=True,
                name=f"script-{script_name}",
            )
            with self._lock:
                self._threads[script_name] = thread
            try:
                thread.start()
            except Exception:
                self._finish(script_name)
                raise
            return True
        return self._run_reserved(script_name, parsed, cancel_event)

    def test_script(self, script_code: str) -> bool:
        """Validate and execute DSL without saving it."""

        self.validate_script(script_code)
        parsed = parse_script(script_code)
        script_name = f"__test__{next(self._test_ids)}"
        cancel_event = self._reserve(script_name)
        assert cancel_event is not None
        return self._run_reserved(script_name, parsed, cancel_event)

    def cancel_script(self, script_name: str) -> bool:
        """Request cancellation; held keys are released by the worker finally block."""

        with self._lock:
            event = self._cancel_events.get(script_name)
            if event is None:
                return False
            event.set()
            return True

    def cancel_all_scripts(self, timeout: float = 1.0) -> None:
        """Cancel all workers and briefly wait for their cleanup."""

        with self._lock:
            events = list(self._cancel_events.values())
            threads = list(self._threads.values())
        for event in events:
            event.set()
        for thread in threads:
            if thread is not threading.current_thread():
                thread.join(max(0.0, timeout))

    def _finish(self, script_name: str) -> None:
        with self._lock:
            self.running_scripts.discard(script_name)
            self._cancel_events.pop(script_name, None)
            self._threads.pop(script_name, None)

    def _safe_key_up(self, key: str) -> None:
        try:
            self._backend.keyUp(key)
        except Exception as error:
            self.log("error", f"Could not release key '{key}': {error}")

    def _run_reserved(
        self,
        script_name: str,
        commands: Sequence[ScriptCommand],
        cancel_event: threading.Event,
    ) -> bool:
        if self._backend is None:
            self.log("error", "Desktop automation backend is unavailable")
            self._finish(script_name)
            return False

        held_keys: List[str] = []
        self.log("info", f"Executing script '{script_name}'")
        success = True
        with _AUTOMATION_LOCK:
            try:
                for command in commands:
                    if cancel_event.is_set():
                        success = False
                        self.log("info", f"Script '{script_name}' cancelled")
                        break
                    self._execute_command(command, held_keys, cancel_event)
            except Exception as error:
                success = False
                self.log("error", f"Error executing script '{script_name}': {error}")
            finally:
                for key in reversed(held_keys):
                    self._safe_key_up(key)
                self._finish(script_name)
        if success:
            self.log("info", f"Script '{script_name}' executed successfully")
        return success

    def _execute_command(
        self,
        command: ScriptCommand,
        held_keys: List[str],
        cancel_event: threading.Event,
    ) -> None:
        operation = command.operation
        arguments = command.arguments
        if operation == "press":
            self._backend.press(arguments[0])
        elif operation == "hold":
            key = arguments[0]
            if key not in held_keys:
                held_keys.append(key)
                self._backend.keyDown(key)
        elif operation == "release":
            key = arguments[0]
            self._backend.keyUp(key)
            if key in held_keys:
                held_keys.remove(key)
        elif operation == "combo":
            pressed: List[str] = []
            try:
                for key in arguments:
                    # Append before keyDown: a backend may fail after the OS has
                    # already observed the key-down event.
                    pressed.append(key)
                    self._backend.keyDown(key)
            finally:
                for key in reversed(pressed):
                    self._safe_key_up(key)
        elif operation == "write":
            self._backend.write(arguments[0])
        elif operation == "delay":
            cancel_event.wait(arguments[0])
        elif operation == "move":
            self._backend.moveTo(arguments[0], arguments[1])
        elif operation == "click":
            if len(arguments) == 1:
                self._backend.click(button=arguments[0])
            else:
                self._backend.click(arguments[1], arguments[2], button=arguments[0])

    def _execute_script_commands(self, script_name: str, commands: List[str]) -> bool:
        """Backward-compatible executor for an explicit list of commands."""

        try:
            parsed = parse_script(_commands_to_code(commands))
        except ScriptValidationError as error:
            self.log("error", f"Invalid script '{script_name}': {error}")
            return False
        if not parsed:
            self.log("warning", f"Script '{script_name}' has no commands")
            return False
        cancel_event = self._reserve(script_name)
        if cancel_event is None:
            return False
        return self._run_reserved(script_name, parsed, cancel_event)


def transform_to_combo(command: str) -> str:
    """Transform legacy ``write`` content into its historical ``$`` format."""

    return "".join(f"${character}" for character in command[len("write ") :])


def execute_script(script: List[str]) -> bool:
    """Backward-compatible module-level execution helper."""

    manager = ScriptManager()
    return manager._execute_script_commands("legacy_script", script)


def save_scripts(scripts: Dict[str, List[str]]) -> bool:
    """Backward-compatible helper routed through the sole scripts repository."""

    manager = ScriptManager()
    normalized, _ = _normalize_scripts(scripts)
    with manager._lock:
        return manager._commit_change(normalized)


def load_scripts() -> Dict[str, List[str]]:
    """Backward-compatible helper using the per-user scripts repository."""

    return ScriptManager().load_scripts()


def create_script(scripts: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Legacy interactive helper retained for source compatibility."""

    script: List[str] = []
    name = input("name: ")
    while True:
        command = input("key: ")
        if command == "exit":
            break
        script.append(command)
    scripts[name] = script
    return scripts
