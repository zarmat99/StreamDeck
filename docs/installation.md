# Installation

## Supported setup

The supported desktop target is 64-bit Windows 10/11 with Python 3.11–3.13 for
source installs. Use a normal (non-administrator) account. Administrator privileges
should not be required to run the application; a board driver or installer may
prompt separately.

OBS Studio must expose a reachable WebSocket server. The default endpoint is
`localhost:4455`, but the actual value comes from OBS. Use authentication even on a
single-user computer and do not reuse the password elsewhere.

## Install from source

```powershell
git clone https://github.com/zarmat99/StreamDeck.git
cd StreamDeck
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
streamdeck-control
```

If PowerShell blocks activation, use `.venv\Scripts\python.exe` explicitly rather
than weakening the machine-wide execution policy.

## Build a local desktop bundle

Install development tools and build from a clean checkout:

```powershell
python -m pip install -e ".[dev]"
python -m PyInstaller --clean --noconfirm streamdeck_control.spec
```

The onedir application is created under `dist\StreamDeck Control`. It must be
tested on a clean Windows account before distribution. A PyInstaller build is not
an installer and does not provide automatic update, Start Menu integration, or
uninstall registration.

For published builds, download only from this repository's Releases page. Compare
the SHA-256 value with `SHA256SUMS.txt`:

```powershell
Get-FileHash ".\StreamDeck-Control-<version>-windows-x64.zip" -Algorithm SHA256
```

If release notes say the executable is signed, also inspect **Properties → Digital
Signatures** and verify the named publisher. An absent or invalid signature must
not be presented as a signed production release.

## Configure OBS

1. Start OBS and open its WebSocket server settings from the Tools menu.
2. Enable the server, keep or record its port, and set a unique password.
3. Start StreamDeck Control and enter host, port, and password on Connections.
4. Connect OBS before mapping scenes or inputs, then verify the reported state.
5. For a remote OBS endpoint, restrict firewall access to the intended network and
   understand that WebSocket traffic leaves the local machine.

The OS credential backend stores the password. JSON configuration keeps only an
empty `"password": ""` compatibility placeholder and never records whether a
credential exists. If no backend is available, the password remains in memory for
that process and must be entered again.

## Flash and connect the reference device

Read [hardware and wiring](hardware-and-wiring.md), choose exactly one input
profile, then run:

```powershell
python -m pip install -e ".[firmware]"
pio run -d firmware -e uno_internal_pullup
pio device list
pio run -d firmware -e uno_internal_pullup -t upload --upload-port COM3
```

Select that COM port and `9600` baud in the application. A successful negotiation
shows protocol and firmware metadata. Map B0–B3 to scenes, P0–P3 to OBS inputs, and
G0–G3 to saved automations. Test each control in a non-live OBS profile.

## Configuration location and backup

Print the exact per-user directory:

```powershell
python -c "from streamdeck_control.utils.config_manager import default_config_dir; print(default_config_dir())"
```

Close the application before copying `settings.json`, `mapping.json`,
`scripts.json`, and their `.bak` files. The OBS password is separate in Windows
Credential Manager and is intentionally not included. Treat automation and mapping
backups as user data; inspect them before transferring to another account.

## Upgrade

1. Back up the per-user JSON directory and note the installed firmware version.
2. Read the target release notes for schema or protocol migration steps.
3. Install the new package/build without deleting local data.
4. Start offline, validate mappings and automations, then connect to rehearsal OBS.
5. Upgrade firmware only when the compatibility table requires it.

Downgrades are not guaranteed because older builds may not understand newer schema
versions. Restore the matching backup or release only after reviewing its migration
notes.

## Uninstall

Remove the virtual environment or packaged application. If a complete local-data
removal is required, close the application, use the path command above, back up any
needed profiles, and delete that application directory manually. Remove the
`streamdeck-controller` / `obs-websocket` entry from Windows Credential Manager.
Uninstalling does not modify OBS or firmware already flashed to the board.
