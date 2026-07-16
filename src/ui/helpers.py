"""Pure UI-domain conversions and input validation (safe in headless tests)."""

from __future__ import annotations

import ipaddress
import re
from typing import Tuple


_HOST_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")
INVALID_SERIAL_PORT_VALUES = {"", "No COM ports available", "Select COM port"}


def validate_obs_values(host_value: str, port_value: str) -> Tuple[str, int]:
    """Validate and normalize values accepted by the OBS controller."""
    host = str(host_value).strip()
    if not host or len(host) > 253 or any(char.isspace() for char in host):
        raise ValueError("Enter a valid OBS host name or IP address.")

    address = host[1:-1] if host.startswith("[") and host.endswith("]") else host
    try:
        ipaddress.ip_address(address)
    except ValueError:
        labels = host.rstrip(".").split(".")
        if not labels or any(not _HOST_LABEL.fullmatch(label) for label in labels):
            raise ValueError("Enter a valid OBS host name or IP address.")

    try:
        port = int(str(port_value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("OBS port must be a number between 1 and 65535.") from exc
    if not 1 <= port <= 65535:
        raise ValueError("OBS port must be between 1 and 65535.")
    return host, port


def validate_serial_values(port_value: str, baud_value: str) -> Tuple[str, int]:
    """Validate and normalize values accepted by the serial controller."""
    raw_port = str(port_value).strip()
    port = raw_port.split(" ", 1)[0]
    if raw_port in INVALID_SERIAL_PORT_VALUES or not port:
        raise ValueError("Select an available serial port.")
    try:
        baud = int(str(baud_value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError("Baud rate must be a positive number.") from exc
    if not 300 <= baud <= 4_000_000:
        raise ValueError("Baud rate must be between 300 and 4,000,000.")
    return port, baud


def db_to_percent(db_value: float) -> float:
    """Map the application's supported -60..0 dB range to 0..100%."""
    return min(100.0, max(0.0, (float(db_value) + 60.0) / 60.0 * 100.0))


def percent_to_db(percent: float) -> float:
    """Map a UI percentage to OBS dB, retaining a hard-silence endpoint."""
    value = min(100.0, max(0.0, float(percent)))
    return -100.0 if value == 0 else (value / 100.0 * 60.0) - 60.0
