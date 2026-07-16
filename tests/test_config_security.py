import json
from pathlib import Path

from src.utils.config_manager import (
    CREDENTIAL_SERVICE,
    OBS_CREDENTIAL_ACCOUNT,
    ConfigManager,
)


class MemoryCredentialStore:
    def __init__(self):
        self.values = {}
        self.set_calls = []
        self.delete_calls = []

    def get_password(self, service, account):
        return self.values.get((service, account))

    def set_password(self, service, account, password):
        self.values[(service, account)] = password
        self.set_calls.append((service, account, password))

    def delete_password(self, service, account):
        self.values.pop((service, account), None)
        self.delete_calls.append((service, account))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_plain_legacy_password_moves_to_credential_store_and_is_scrubbed(tmp_path):
    legacy = {
        "custom_section": {"preserved": True},
        "connection": {
            "obs_data": {
                "host": "obs.local",
                "port": 4456,
                "password": "correct horse battery staple",
            },
            "serial_data": {"com_port": "COM7", "baud_rate": 115200},
        },
        "script": {"legacy": ["press enter"]},
        "mapping": {"B0": "Intro", "X-custom": "preserve me"},
    }
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps(legacy), encoding="utf-8")
    store = MemoryCredentialStore()

    manager = ConfigManager(tmp_path, credential_store=store)

    assert manager.settings["connection"]["obs_data"]["password"] == (
        "correct horse battery staple"
    )
    assert store.values[(CREDENTIAL_SERVICE, OBS_CREDENTIAL_ACCOUNT)] == (
        "correct horse battery staple"
    )
    assert manager.settings["connection"]["obs_data"]["port"] == "4456"
    assert manager.settings["connection"]["serial_data"]["baud_rate"] == "115200"
    assert manager.settings["custom_section"] == {"preserved": True}
    assert manager.settings["mapping"]["B0"] == "Intro"
    assert manager.settings["mapping"]["X-custom"] == "preserve me"

    for path in (settings_path, tmp_path / "settings.json.bak"):
        text = path.read_text(encoding="utf-8")
        assert "correct horse battery staple" not in text
        payload = read_json(path)
        assert payload["connection"]["obs_data"]["password"] == ""
        assert payload["script"] == {}
        assert "mapping" not in payload


def test_password_is_memory_only_when_no_credential_store_exists(tmp_path):
    manager = ConfigManager(tmp_path, credential_store=None)
    assert manager.credential_persistence_available is False
    manager.settings["connection"]["obs_data"]["password"] = "ephemeral"

    assert manager.save_settings() is True
    assert manager.settings["connection"]["obs_data"]["password"] == "ephemeral"
    assert read_json(manager.config_path)["connection"]["obs_data"]["password"] == ""
    assert "ephemeral" not in Path(manager.config_path).read_text(encoding="utf-8")

    reloaded = ConfigManager(tmp_path, credential_store=None)
    assert reloaded.settings["connection"]["obs_data"]["password"] == ""


def test_keyring_value_is_loaded_and_empty_password_deletes_it(tmp_path):
    store = MemoryCredentialStore()
    store.values[(CREDENTIAL_SERVICE, OBS_CREDENTIAL_ACCOUNT)] = "from-keyring"
    manager = ConfigManager(tmp_path, credential_store=store)
    assert manager.credential_persistence_available is True

    assert manager.settings["connection"]["obs_data"]["password"] == "from-keyring"

    manager.settings["connection"]["obs_data"]["password"] = ""
    manager.save_settings()
    assert (CREDENTIAL_SERVICE, OBS_CREDENTIAL_ACCOUNT) not in store.values
    assert store.delete_calls == [(CREDENTIAL_SERVICE, OBS_CREDENTIAL_ACCOUNT)]


def test_fixed_key_legacy_ciphertext_is_not_decrypted_and_is_scrubbed(tmp_path):
    encrypted = "encrypted:legacy-fixed-key-material"
    settings = {
        "connection": {"obs_data": {"password": encrypted}},
        "mapping": {"B3": "Outro"},
    }
    (tmp_path / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    # Include a legacy backup too: initialization must leave neither copy with
    # credential material.
    (tmp_path / "settings.json.bak").write_text(json.dumps(settings), encoding="utf-8")

    manager = ConfigManager(tmp_path, credential_store=None)

    assert manager.settings["connection"]["obs_data"]["password"] == ""
    assert manager.settings["mapping"]["B3"] == "Outro"
    assert encrypted not in (tmp_path / "settings.json").read_text(encoding="utf-8")
    assert encrypted not in (tmp_path / "settings.json.bak").read_text(encoding="utf-8")


def test_mapping_write_has_backup_and_recovers_corrupt_primary(tmp_path):
    manager = ConfigManager(tmp_path, credential_store=None)
    manager.settings["mapping"]["B0"] = "First"
    manager.save_mapping()
    manager.settings["mapping"]["B0"] = "Second"
    manager.save_mapping()

    assert read_json(f"{manager.mapping_path}.bak")["B0"] == "First"
    Path(manager.mapping_path).write_text("{broken", encoding="utf-8")

    recovered = manager.load_mapping()

    assert recovered["B0"] == "First"
    assert read_json(manager.mapping_path)["B0"] == "First"
    assert read_json(f"{manager.mapping_path}.bak")["B0"] == "First"


def test_mapping_file_overrides_embedded_mapping_but_keeps_defaults(tmp_path):
    (tmp_path / "settings.json").write_text(
        json.dumps({"mapping": {"B0": "embedded", "custom": "embedded-value"}}),
        encoding="utf-8",
    )
    (tmp_path / "mapping.json").write_text(
        json.dumps({"B0": "dedicated", "custom-2": "dedicated-value"}),
        encoding="utf-8",
    )

    manager = ConfigManager(tmp_path, credential_store=None)

    assert manager.settings["mapping"]["B0"] == "dedicated"
    assert manager.settings["mapping"]["custom"] == "embedded-value"
    assert manager.settings["mapping"]["custom-2"] == "dedicated-value"
    assert set(f"B{index}" for index in range(4)) <= manager.settings["mapping"].keys()


def test_config_manager_never_writes_scripts_repository(tmp_path):
    scripts_path = tmp_path / "scripts.json"
    scripts_path.write_text('{"owned": ["press enter"]}', encoding="utf-8")
    manager = ConfigManager(tmp_path, credential_store=None)
    manager.settings["script"] = {"wrong-writer": ["press escape"]}

    assert manager.save_scripts() is False
    manager.save_settings()

    assert read_json(scripts_path) == {"owned": ["press enter"]}
    assert read_json(manager.config_path)["script"] == {}


def test_invalid_runtime_values_are_normalized_before_startup(tmp_path):
    (tmp_path / "settings.json").write_text(
        json.dumps(
            {
                "connection": {
                    "obs_data": {"host": "", "port": "not-a-port"},
                    "serial_data": {"baud_rate": -1},
                    "auto_connect": 0,
                },
                "ui": {"theme": "neon", "font_size": "giant", "language": ""},
                "logs": {"level": "trace", "max_files": 999},
            }
        ),
        encoding="utf-8",
    )

    manager = ConfigManager(config_dir=tmp_path, credential_store=None)

    assert manager.settings["connection"]["obs_data"]["host"] == "localhost"
    assert manager.settings["connection"]["obs_data"]["port"] == "4455"
    assert manager.settings["connection"]["serial_data"]["baud_rate"] == "9600"
    assert manager.settings["ui"] == {
        "theme": "dark",
        "font_size": "medium",
        "language": "en",
    }
    assert manager.settings["logs"]["level"] == "info"
    assert manager.settings["logs"]["max_files"] == 20
