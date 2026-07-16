# Testing and quality gates

## Local environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
pre-commit install --hook-type pre-commit --hook-type pre-push
```

Unit tests must run without OBS, attached hardware, network access, or a visible
desktop. External clients and automation backends are replaced with deterministic
fakes. A test that uses real hardware belongs in the manual acceptance suite.

## Required desktop checks

```powershell
python scripts/scan_secrets.py
python scripts/check_release.py
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest --cov=src --cov-report=term-missing --cov-report=xml
python -m pip_audit --strict --requirement requirements.txt
python -m build --no-isolation
python -m twine check dist/*
python -m PyInstaller --clean --noconfirm streamdeck_control.spec
python scripts/check_pyinstaller.py
```

The configured 35% coverage failure floor prevents large accidental regressions;
it is not the quality target. Changed domain, persistence, parser, and lifecycle
code should reach at least 80% branch coverage with error paths. UI rendering may
use integration tests and a documented manual matrix where automation is fragile.

The local secret scan is intentionally fast and dependency-free. It examines
tracked and non-ignored untracked text files, prints no matched value, and catches
only common formats. A passing result does not certify that no secret exists.

`pyproject.toml` is the canonical dependency declaration. `requirements.txt`
mirrors only its runtime dependencies for compatibility and auditing;
`check_release.py` fails if the two lists diverge. Broadly supported Python
3.11–3.13 metadata cannot be represented truthfully by one platform-specific
freeze, so the repository does not pretend that a single developer lock applies
to every interpreter. Release builds use one declared Windows/Python target and
publish the exact resolved environment as `BUILD-ENVIRONMENT.txt`. Consequently,
an old executable is traceable but is not claimed to be byte-for-byte reproducible
until target-specific, hash-locked dependency files are maintained.

`python -m build --no-isolation` is the offline packaging check after development
requirements have been installed. A fresh CI/release environment still installs
the declared build tools first, then uses the same no-isolation build so an
unexpected second dependency download cannot hide missing build requirements.
`check_pyinstaller.py` also fails the packaging gate when Tkinter, the application
package, the executable, or CustomTkinter assets were omitted from the bundle.

## Firmware checks

```powershell
pio run -d firmware -e uno_active_high
pio run -d firmware -e uno_internal_pullup
```

Both electrical profiles must compile with warnings enabled. Generated `.hex`,
`.elf`, and `.pio` output is never committed. For firmware behavior, exercise the
session transcript in [protocol.md](protocol.md) and the bench checklist in
[hardware-and-wiring.md](hardware-and-wiring.md).

## Manual desktop matrix

At minimum, a release candidate is tested on a clean standard-user Windows account
at 100%, 150%, and 200% display scaling with:

- a supported OBS version, password authentication, and localhost endpoint;
- invalid password, unavailable host, OBS restart, and network interruption;
- device absent, wrong port, board reset, USB removal, and repeated reconnect;
- all twelve mapped controls plus dedicated stream/record and both LEDs;
- empty, valid, invalid, failing, duplicate, and cancelled automations;
- first run, corrupt primary JSON, valid backup recovery, upgrade, and clean exit;
- a path/account containing spaces and non-ASCII characters.

Record OS, OBS, desktop version, firmware version, hardware profile, result, and
tester in release evidence. Never use a production stream key.

## Soak and failure-injection tests

Run the release build for at least eight hours with OBS and the device connected.
Periodically restart OBS, reset the board, unplug/replug USB, move all analog
controls, and trigger mappings. Acceptance requires no UI freeze, runaway log,
unbounded queue, duplicate transport workers, stuck keys, or unrecovered connection.

Use a serial fuzzer/fake transport to send empty lines, NULs, oversized data,
invalid UTF-8, partial messages, unknown commands, invalid identifiers, and values
outside the ADC range. Use concurrent fake callbacks to verify registry and
shutdown safety.

## CI behavior

`ci.yml` runs the desktop suite on Windows with Python 3.11, 3.12, and 3.13, then
builds Python and PyInstaller artifacts. `firmware.yml` compiles both PlatformIO
profiles. Dependency auditing runs separately so findings are visible and can be
triaged without silently changing application code. Pull requests should require
these workflows through branch protection.
