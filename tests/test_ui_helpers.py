"""Headless tests for UI-domain validation and value conversion."""

import pytest

from src.ui.helpers import (
    db_to_percent,
    percent_to_db,
    validate_obs_values,
    validate_serial_values,
)


@pytest.mark.parametrize(
    ("host", "port", "expected"),
    [
        (" localhost ", "4455", ("localhost", 4455)),
        ("127.0.0.1", 1, ("127.0.0.1", 1)),
        ("[::1]", "65535", ("[::1]", 65535)),
        ("obs-studio.local", "4455", ("obs-studio.local", 4455)),
    ],
)
def test_validate_obs_values(host, port, expected):
    assert validate_obs_values(host, port) == expected


@pytest.mark.parametrize(
    ("host", "port"),
    [("", "4455"), ("bad host", "4455"), ("localhost", 0), ("localhost", 65536)],
)
def test_validate_obs_values_rejects_invalid_input(host, port):
    with pytest.raises(ValueError):
        validate_obs_values(host, port)


def test_validate_serial_values_normalizes_combobox_label():
    assert validate_serial_values("COM7 (USB Serial)", "115200") == ("COM7", 115200)


@pytest.mark.parametrize("port", ["", "Select COM port", "No COM ports available"])
def test_validate_serial_values_requires_device(port):
    with pytest.raises(ValueError):
        validate_serial_values(port, "9600")


def test_volume_conversions_cover_endpoints_and_clamp():
    assert db_to_percent(-100) == 0
    assert db_to_percent(-60) == 0
    assert db_to_percent(-30) == 50
    assert db_to_percent(0) == 100
    assert percent_to_db(-1) == -100
    assert percent_to_db(0) == -100
    assert percent_to_db(50) == -30
    assert percent_to_db(101) == 0
