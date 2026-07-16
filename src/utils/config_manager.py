"""Configuration persistence and credential handling.

Configuration files deliberately never contain the OBS password.  When the
optional :mod:`keyring` package is available, the password is stored in the
operating system credential store; otherwise it lives in memory for the
current process only.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import tempfile
import threading
from typing import Any, Callable, Dict, Mapping, Optional, Protocol, Tuple, Union


APP_NAME = "StreamDeckController"
APP_AUTHOR = "StreamDeckController"
CREDENTIAL_SERVICE = "streamdeck-controller"
OBS_CREDENTIAL_ACCOUNT = "obs-websocket"
SCHEMA_VERSION = 1


class CredentialStore(Protocol):
    """Small subset of the keyring API used by :class:`ConfigManager`."""

    def get_password(self, service: str, account: str) -> Optional[str]: ...

    def set_password(self, service: str, account: str, password: str) -> None: ...

    def delete_password(self, service: str, account: str) -> None: ...


class _KeyringStore:
    """Adapter kept private so keyring remains an optional dependency."""

    def __init__(self, module: Any) -> None:
        self._module = module

    def get_password(self, service: str, account: str) -> Optional[str]:
        return self._module.get_password(service, account)

    def set_password(self, service: str, account: str, password: str) -> None:
        self._module.set_password(service, account, password)

    def delete_password(self, service: str, account: str) -> None:
        self._module.delete_password(service, account)


_AUTO_CREDENTIAL_STORE = object()


def default_config_dir() -> str:
    """Return a per-user writable configuration directory.

    ``platformdirs`` is preferred when installed.  The fallback follows the
    native environment on Windows and XDG conventions elsewhere.
    """

    try:
        from platformdirs import user_config_dir

        return user_config_dir(APP_NAME, APP_AUTHOR)
    except (ImportError, OSError):
        pass

    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if base:
            return str(Path(base) / APP_NAME)

    base = os.environ.get("XDG_CONFIG_HOME")
    if base:
        return str(Path(base) / APP_NAME)
    return str(Path.home() / ".config" / APP_NAME)


def _default_settings() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "connection": {
            "obs_data": {
                "host": "localhost",
                "port": "4455",
                "password": "",
            },
            "serial_data": {"com_port": None, "baud_rate": "9600"},
            "auto_connect": False,
        },
        "online": {},
        # Retained in memory for compatibility. ScriptManager is the sole
        # owner of scripts.json and ConfigManager never writes that file.
        "script": {},
        "mapping": {
            "B0": None,
            "B1": None,
            "B2": None,
            "B3": None,
            "P0": None,
            "P1": None,
            "P2": None,
            "P3": None,
            "G0": None,
            "G1": None,
            "G2": None,
            "G3": None,
        },
        "ui": {"theme": "dark", "font_size": "medium", "language": "en"},
        "logs": {
            "level": "info",
            "file_enabled": True,
            "console_enabled": False,
            "max_files": 5,
        },
    }


def _deep_merge(
    defaults: Mapping[str, Any], loaded: Mapping[str, Any]
) -> Dict[str, Any]:
    """Merge defaults without discarding unknown user configuration keys."""

    result: Dict[str, Any] = copy.deepcopy(dict(loaded))
    for key, default_value in defaults.items():
        if key not in result:
            result[key] = copy.deepcopy(default_value)
        elif isinstance(default_value, Mapping):
            if isinstance(result[key], Mapping):
                result[key] = _deep_merge(default_value, result[key])
            else:
                result[key] = copy.deepcopy(default_value)
    return result


def _read_json(path: Path) -> Tuple[Optional[Any], bool]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle), True
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeError):
        return None, False


def read_json_with_backup(
    path: Union[str, os.PathLike[str]],
) -> Tuple[Optional[Any], bool]:
    """Read JSON, falling back to ``<name>.bak``.

    Returns ``(payload, recovered_from_backup)``.  A missing or invalid primary
    and backup produces ``(None, False)``.
    """

    target = Path(path)
    payload, valid = _read_json(target)
    if valid:
        return payload, False
    payload, valid = _read_json(Path(f"{target}.bak"))
    return (payload, True) if valid else (None, False)


def _replace_json(path: Path, payload: Any) -> None:
    """Replace one JSON file atomically with a flushed temporary file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def atomic_write_json(
    path: Union[str, os.PathLike[str]],
    payload: Any,
    backup_transform: Optional[Callable[[Any], Any]] = None,
) -> None:
    """Atomically write JSON and retain the last valid version as ``.bak``.

    Invalid current files are never copied over a known-good backup.  A
    transform can redact sensitive fields before backup creation.
    """

    target = Path(path)
    backup = Path(f"{target}.bak")
    current, valid = _read_json(target)
    if valid:
        backup_payload = copy.deepcopy(current)
        if backup_transform is not None:
            backup_payload = backup_transform(backup_payload)
        _replace_json(backup, backup_payload)
    else:
        existing_backup, backup_valid = _read_json(backup)
        if not backup_valid:
            backup_payload = copy.deepcopy(payload)
            if backup_transform is not None:
                backup_payload = backup_transform(backup_payload)
            _replace_json(backup, backup_payload)
        elif backup_transform is not None:
            sanitized_backup = backup_transform(copy.deepcopy(existing_backup))
            if existing_backup != sanitized_backup:
                _replace_json(backup, sanitized_backup)
    _replace_json(target, payload)


def _normalize_mapping(value: Any) -> Dict[str, Any]:
    defaults = _default_settings()["mapping"]
    if not isinstance(value, Mapping):
        return defaults
    result = copy.deepcopy(defaults)
    result.update(copy.deepcopy(dict(value)))
    return result


def _normalize_settings(value: Any) -> Dict[str, Any]:
    loaded = value if isinstance(value, Mapping) else {}
    settings = _deep_merge(_default_settings(), loaded)
    settings["schema_version"] = SCHEMA_VERSION

    obs_data = settings["connection"]["obs_data"]
    host = obs_data.get("host")
    obs_data["host"] = str(host) if host not in (None, "") else "localhost"
    try:
        port = int(str(obs_data.get("port", "4455")))
    except (TypeError, ValueError):
        port = 4455
    obs_data["port"] = str(port if 1 <= port <= 65535 else 4455)
    if not isinstance(obs_data.get("password"), str):
        obs_data["password"] = ""

    serial_data = settings["connection"]["serial_data"]
    com_port = serial_data.get("com_port")
    serial_data["com_port"] = None if com_port in (None, "") else str(com_port)
    try:
        baud_rate = int(str(serial_data.get("baud_rate", "9600")))
    except (TypeError, ValueError):
        baud_rate = 9600
    serial_data["baud_rate"] = str(baud_rate if 300 <= baud_rate <= 4_000_000 else 9600)
    settings["connection"]["auto_connect"] = bool(
        settings["connection"].get("auto_connect", False)
    )

    settings["mapping"] = _normalize_mapping(settings.get("mapping"))
    for section in ("online", "script", "ui", "logs"):
        if not isinstance(settings.get(section), Mapping):
            settings[section] = copy.deepcopy(_default_settings()[section])

    ui = settings["ui"]
    if ui.get("theme") not in {"dark", "light", "system"}:
        ui["theme"] = "dark"
    if ui.get("font_size") not in {"small", "medium", "large"}:
        ui["font_size"] = "medium"
    if not isinstance(ui.get("language"), str) or not ui["language"].strip():
        ui["language"] = "en"

    logs = settings["logs"]
    if logs.get("level") not in {"debug", "info", "warning", "error", "critical"}:
        logs["level"] = "info"
    logs["file_enabled"] = bool(logs.get("file_enabled", True))
    logs["console_enabled"] = bool(logs.get("console_enabled", False))
    try:
        max_files = int(logs.get("max_files", 5))
    except (TypeError, ValueError):
        max_files = 5
    logs["max_files"] = min(20, max(1, max_files))
    return settings


def _settings_for_disk(value: Any) -> Dict[str, Any]:
    """Return a normalized copy with every credential field redacted."""

    settings = _normalize_settings(value)
    settings["connection"]["obs_data"]["password"] = ""
    # Hardware mappings have their own atomically-written repository. Legacy
    # embedded mappings are migrated by ``load_mapping`` and then omitted here
    # so there is exactly one persisted source of truth.
    settings.pop("mapping", None)
    # Historical releases duplicated automations inside settings.json. Keep
    # any loaded value in memory for compatibility, but only ScriptManager may
    # persist automation definitions.
    settings["script"] = {}
    return settings


class ConfigManager:
    """Manage non-secret settings, mapping, and the optional OS credential."""

    def __init__(
        self,
        config_dir: Optional[Union[str, os.PathLike[str]]] = None,
        credential_store: Any = _AUTO_CREDENTIAL_STORE,
    ) -> None:
        self.config_dir = str(Path(config_dir or default_config_dir()))
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)

        self.config_path = os.path.join(self.config_dir, "settings.json")
        self.mapping_path = os.path.join(self.config_dir, "mapping.json")
        # Kept as a discoverable path for callers constructing ScriptManager.
        self.scripts_path = os.path.join(self.config_dir, "scripts.json")
        self._lock = threading.RLock()
        self.credential_store: Optional[CredentialStore] = self._resolve_store(
            credential_store
        )
        self.last_credential_error: Optional[Exception] = None
        self.settings = _default_settings()

        self.load_settings()
        self.load_mapping()

    @property
    def credential_persistence_available(self) -> bool:
        """Whether the current OS credential backend is usable.

        A backend can be importable but unavailable for the current session, so
        the most recent keyring operation is part of this health signal.
        """

        return self.credential_store is not None and self.last_credential_error is None

    @staticmethod
    def _resolve_store(store: Any) -> Optional[CredentialStore]:
        if store is not _AUTO_CREDENTIAL_STORE:
            return store
        try:
            import keyring

            return _KeyringStore(keyring)
        except (ImportError, OSError):
            return None

    def _get_stored_password(self) -> Optional[str]:
        if self.credential_store is None:
            return None
        try:
            return self.credential_store.get_password(
                CREDENTIAL_SERVICE, OBS_CREDENTIAL_ACCOUNT
            )
        except Exception as error:  # keyring backends expose several error types
            self.last_credential_error = error
            return None

    def _persist_password(self, password: str) -> bool:
        if self.credential_store is None:
            return False
        try:
            if password:
                self.credential_store.set_password(
                    CREDENTIAL_SERVICE, OBS_CREDENTIAL_ACCOUNT, password
                )
            else:
                try:
                    self.credential_store.delete_password(
                        CREDENTIAL_SERVICE, OBS_CREDENTIAL_ACCOUNT
                    )
                except Exception:
                    # Deleting a non-existent credential is harmless and some
                    # keyring backends report it as an error.
                    pass
            self.last_credential_error = None
            return True
        except Exception as error:
            self.last_credential_error = error
            return False

    def _scrub_backup(self) -> None:
        backup = Path(f"{self.config_path}.bak")
        if not backup.exists():
            return
        payload, valid = _read_json(backup)
        if valid:
            sanitized = _settings_for_disk(payload)
            if payload != sanitized:
                _replace_json(backup, sanitized)
        else:
            # An unreadable legacy backup cannot be proven secret-free.
            try:
                backup.unlink()
            except FileNotFoundError:
                pass

    def save_settings(self) -> bool:
        """Persist settings atomically while storing no password in JSON."""

        with self._lock:
            password = self.settings["connection"]["obs_data"].get("password", "")
            password = password if isinstance(password, str) else ""
            self._persist_password(password)
            on_disk = _settings_for_disk(self.settings)
            atomic_write_json(self.config_path, on_disk, _settings_for_disk)
            self._scrub_backup()
            return True

    def load_settings(self) -> Dict[str, Any]:
        """Load, migrate and normalize settings without exposing disk secrets."""

        with self._lock:
            path = Path(self.config_path)
            raw, recovered = read_json_with_backup(path)
            normalized = _normalize_settings(raw)
            disk_password = normalized["connection"]["obs_data"].get("password", "")

            # Fixed-key ciphertext from old releases is intentionally not
            # decrypted. It is scrubbed and must be re-entered/rotated.
            legacy_plain_password = ""
            if isinstance(disk_password, str) and disk_password:
                if not disk_password.startswith("encrypted:"):
                    legacy_plain_password = disk_password

            stored_password = self._get_stored_password()
            password = stored_password or legacy_plain_password
            normalized["connection"]["obs_data"]["password"] = password
            self.settings = normalized

            if legacy_plain_password and not stored_password:
                self._persist_password(legacy_plain_password)

            sanitized = _settings_for_disk(normalized)
            if raw != sanitized or recovered or not path.exists():
                atomic_write_json(path, sanitized, _settings_for_disk)
            self._scrub_backup()
            return self.settings

    def save_mapping(self) -> bool:
        """Persist the complete mapping atomically."""

        with self._lock:
            mapping = _normalize_mapping(self.settings.get("mapping"))
            self.settings["mapping"] = mapping
            atomic_write_json(self.mapping_path, mapping)
            return True

    def load_mapping(self) -> Dict[str, Any]:
        """Load mapping with backup recovery and embedded-settings fallback."""

        with self._lock:
            path = Path(self.mapping_path)
            raw, recovered = read_json_with_backup(path)
            mapping = _normalize_mapping(self.settings.get("mapping"))
            if isinstance(raw, Mapping):
                # The dedicated mapping wins on conflicts, while entries that
                # existed only in legacy embedded settings are retained.
                mapping.update(copy.deepcopy(dict(raw)))
            self.settings["mapping"] = mapping
            if raw != mapping or recovered or not path.exists():
                atomic_write_json(path, mapping)
            return mapping

    def save_scripts(self) -> bool:
        """Deprecated compatibility no-op; ScriptManager is the sole writer."""

        return False

    def load_scripts(self) -> Dict[str, Any]:
        """Return legacy in-memory data without reading or writing scripts.json."""

        scripts = self.settings.get("script", {})
        return copy.deepcopy(dict(scripts)) if isinstance(scripts, Mapping) else {}
