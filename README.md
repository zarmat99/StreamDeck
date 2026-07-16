# StreamDeck Control

[![Desktop CI](https://github.com/zarmat99/StreamDeck/actions/workflows/ci.yml/badge.svg)](https://github.com/zarmat99/StreamDeck/actions/workflows/ci.yml)
[![Firmware CI](https://github.com/zarmat99/StreamDeck/actions/workflows/firmware.yml/badge.svg)](https://github.com/zarmat99/StreamDeck/actions/workflows/firmware.yml)

StreamDeck Control is a Windows-first desktop application and reference firmware
for a physical OBS Studio control surface. Four scene buttons, four analog volume
controls, four automation buttons, and dedicated streaming/recording controls are
connected through a versioned serial protocol.

> **Project status: alpha.** Use it in rehearsal environments before relying on it
> during a live production. The source is currently published under a temporary
> all-rights-reserved license; it is not an open-source license.

This independent project is not affiliated with, endorsed by, or sponsored by
Elgato or Corsair. “Stream Deck” may be a trademark of its respective owner. See
[name and licensing considerations](docs/name-and-licensing.md) before public or
commercial distribution.

## What it provides

- OBS WebSocket control for scenes, source volume, mute, streaming, and recording.
- An Arduino Uno-compatible reference device with debouncing, analog filtering,
  capability discovery, and automatic host reconnection.
- A declarative automation language; automation text is validated and Python code
  is never evaluated.
- Per-user configuration with atomic writes and recovery backups.
- OBS credentials stored through the operating-system credential store, never in
  the JSON configuration.
- Thread-isolated OBS and serial I/O with UI updates marshalled to the Tk thread.

## Requirements

- Windows 10 or 11 for the supported desktop experience.
- CPython 3.11, 3.12, or 3.13 when running from source.
- OBS Studio with its WebSocket server enabled.
- An Arduino Uno-compatible ATmega328P board for the reference firmware, or a
  compatible device implementing [protocol v1](docs/protocol.md).

## Quick start from source

```powershell
git clone https://github.com/zarmat99/StreamDeck.git
cd StreamDeck
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
streamdeck-control
```

In OBS, open **Tools → WebSocket Server Settings**, enable the server, and set a
password. Use the application's Connections page to select that endpoint and the
serial port. The password is saved only when a working OS credential backend is
available.

For complete source, executable, OBS, and firmware instructions, see the
[installation guide](docs/installation.md).

## Reference firmware

The recommended new wiring uses inputs connected to ground and the Arduino's
internal pull-ups:

```powershell
python -m pip install -e ".[firmware]"
pio run -d firmware -e uno_internal_pullup
```

Use `uno_active_high` only for the original external-pulldown circuit. Flashing the
wrong electrical profile produces inverted or floating controls. Read the
[hardware and wiring guide](docs/hardware-and-wiring.md) first.

## Development

```powershell
python -m pip install -r requirements-dev.txt
pre-commit install --hook-type pre-commit --hook-type pre-push
python -m pytest --cov=src --cov-report=term-missing
python scripts/scan_secrets.py
```

The complete quality and release commands are documented in
[testing](docs/testing.md) and [releasing](docs/releasing.md). Contributions must
follow [CONTRIBUTING.md](CONTRIBUTING.md).

## Documentation

| Topic | Document |
| --- | --- |
| Components, state, and thread boundaries | [Architecture](docs/architecture.md) |
| Host/device messages and compatibility | [Serial protocol](docs/protocol.md) |
| Pin map and electrical profiles | [Hardware and wiring](docs/hardware-and-wiring.md) |
| Source, OBS, firmware, and executable setup | [Installation](docs/installation.md) |
| Automation commands and safety | [Automations](docs/automations.md) |
| Local and CI verification | [Testing](docs/testing.md) |
| Common recovery procedures | [Troubleshooting](docs/troubleshooting.md) |
| Maintainer release checklist | [Releasing](docs/releasing.md) |

## Security, privacy, and support

Do not put passwords, API tokens, private keys, or real production configuration
in an issue or commit. Report vulnerabilities privately according to
[SECURITY.md](SECURITY.md). The application has no telemetry; local data handling
is described in [PRIVACY.md](PRIVACY.md). For usage help, see
[SUPPORT.md](SUPPORT.md).

## License

Copyright © 2026 StreamDeck Control contributors. All rights reserved. The
temporary [LICENSE](LICENSE) does not grant rights to copy, modify, redistribute,
or sell the software. A definitive license and product name must be selected and
reviewed before broader distribution.
