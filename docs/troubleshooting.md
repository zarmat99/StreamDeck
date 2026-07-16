# Troubleshooting

Start with the smallest isolated test: application only, OBS only, then the serial
device. Do not change wiring while USB power is connected. Redact every log before
sharing it.

## Application does not start

- Confirm `python --version` is 3.11–3.13 and that the intended virtual environment
  is active.
- Run `python -m pip check` and reinstall with `python -m pip install -e .`.
- From source, start with `streamdeck-control` so package imports match production.
- For a packaged build, extract the complete directory; do not run only the `.exe`
  copied away from its bundled files.
- Check the rotating application log in the per-user data location, removing any
  host, port, scene/input name, path, or personal data before sharing.

## OBS does not connect

1. Verify OBS is running and its WebSocket server is enabled.
2. Copy host and port from OBS; use `localhost` only when both programs are on the
   same machine.
3. Re-enter the password. An old OS credential may differ from a password changed
   in OBS.
4. Temporarily test with the local firewall rule and network profile reviewed; do
   not expose the WebSocket port to the public internet.
5. Restart OBS and confirm the application reconnects without creating duplicate
   status events.

Authentication failures are not fixed by deleting mappings or reflashing firmware.

## Serial device is missing or fails negotiation

- Use `pio device list` or Windows Device Manager to identify the actual COM port.
- Close Arduino Serial Monitor and every program that may hold the port.
- Select 9600 baud and wait for the board's reset delay.
- Confirm the device replies to `HELLO 1` with `READY 1 ...` and to `START` with
  `ACK START`.
- Try a known data-capable USB cable and a direct port; many charging cables expose
  no serial data.
- Reflash the matching PlatformIO environment and retest before changing app code.

## Buttons are inverted, repeated, or always active

The firmware electrical profile does not match the circuit or an input is floating.
For `uno_internal_pullup`, every switch connects input to ground. For
`uno_active_high`, every released input needs an external pulldown and the switch
drives it to 5 V. Inspect common ground and bounce at the hardware before changing
debounce constants.

## Potentiometer is reversed or noisy

Swap the two outer potentiometer terminals to reverse direction; never move the
wiper away from its analog pin. Confirm common ground, short analog leads, stable
supply, and full endpoint travel. A value that chatters while untouched indicates
an electrical problem even if software filtering hides some updates.

## Controls connect but do nothing

- Confirm both OBS and serial status are connected.
- Verify B/P/G identifiers are mapped and the target scene/input/automation still
  exists under the exact saved name.
- Test with a new mapping after refreshing OBS objects.
- Inspect whether the device advertised B0–B3, P0–P3, and G0–G3 capabilities.
- Keep OBS in a rehearsal profile while testing stream/record controls.

## Automation fails or leaves a key held

Validate the automation in the editor and test it with an inert window focused.
Check key names and screen coordinates, cancel duplicate/running instances, and
use PyAutoGUI's fail-safe. The manager attempts key cleanup after error or
cancellation; if the OS still sees a held modifier, physically press and release
that key once, stop automation use, and preserve a redacted diagnostic.

## Credential is not remembered

The JSON file intentionally never stores an OBS password. Windows Credential
Manager must offer a working backend through `keyring`; otherwise the application
uses the value only in memory. Remove a stale `streamdeck-controller` /
`obs-websocket` entry and save it again. Do not work around this by writing a plain
password into `settings.json`.

## Reset local state

First print the exact directory:

```powershell
python -c "from streamdeck_control.utils.config_manager import default_config_dir; print(default_config_dir())"
```

Close the application. Copy that directory to a safe temporary location, then
rename the original directory rather than immediately deleting it. Start once to
create defaults. If the fault disappears, re-create settings and import only
reviewed mappings/automations; do not restore a corrupt file wholesale. Delete the
old copy only after verification. Credentials are managed separately in Windows
Credential Manager.

If the problem remains, open a report following [SUPPORT.md](../SUPPORT.md). Use
[SECURITY.md](../SECURITY.md) for crashes or behavior that may cross a security
boundary.
