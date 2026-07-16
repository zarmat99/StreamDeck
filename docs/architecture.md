# Architecture

## Context and goals

StreamDeck Control translates physical controls into OBS WebSocket operations and
validated local desktop automations. Its primary reliability rule is that a lost
OBS or USB connection must not freeze the interface or create an unbounded number
of reconnect workers.

The supported application boundary is Windows, one OBS WebSocket endpoint, and one
serial control surface. The reference firmware targets an Arduino Uno-compatible
ATmega328P. Additional operating systems, multiple OBS instances, plug-in loading,
and arbitrary code execution are not current product commitments.

## Component view

```text
┌──────────────────────── Tk main thread ─────────────────────────┐
│ CustomTkinter pages → StreamDeckApp → UI action/result queue    │
└──────────────────────────────┬───────────────────────────────────┘
                               │ commands / immutable results
             ┌─────────────────┼──────────────────┐
             ▼                 ▼                  ▼
       OBSController     SerialController    ScriptManager
       health worker     reader + writer     automation workers
             │                 │                  │
        OBS WebSocket      USB serial          PyAutoGUI
                               │
                       reference firmware

                ConfigManager + OS keyring
                  atomic JSON / credentials
```

| Component | Responsibility | Must not do |
| --- | --- | --- |
| `StreamDeckApp` | Service construction, navigation, callback wiring, UI queue, coordinated shutdown | Block the Tk thread on long I/O |
| UI pages | Render state and validate user input | Access Tk widgets from worker callbacks |
| `OBSController` | Serialize WebSocket calls, translate events, health-check and reconnect | Create a new health worker for every failure |
| `SerialController` | Negotiate protocol, parse bounded lines, queue writes, reconnect transport | Trust malformed device messages or update widgets |
| `ScriptManager` | Validate, persist, run, cancel, and de-duplicate declarative automations | Evaluate Python or shell input |
| `ConfigManager` | Own settings/mapping persistence and credentials | Persist OBS passwords in JSON or write the automation repository |
| Firmware | Debounce controls, filter ADC values, advertise capabilities, drive LEDs | Block while a control remains pressed |

The repository stores its Python package in `src/`, but the distribution maps that
directory to the installed package name `streamdeck_control`. The console entry
point is `streamdeck_control.app:run`.

## Threading and lifecycle invariants

Tkinter is single-threaded. Controller and automation callbacks may originate on
worker threads, so user-interface changes are published to the application UI
queue and drained with `after()` on the main thread.

Each connection adapter owns its entire transport lifecycle:

- OBS calls are serialized. One health worker performs bounded exponential
  reconnects and is joined during disconnect.
- Serial uses one reader and one writer for an active lifecycle. Commands use
  thread-safe queues, and reconnect happens within the owning lifecycle.
- Shutdown first prevents new work, then disconnects transports, cancels or joins
  managed work, and finally destroys the UI.

Callbacks are copied under locks and invoked outside those locks. A callback can
therefore call a controller method without deadlocking the registry.

## State and persistence

`platformdirs` selects a writable per-user configuration directory. To print the
exact directory for the active account:

```powershell
python -c "from streamdeck_control.utils.config_manager import default_config_dir; print(default_config_dir())"
```

The directory contains these logical stores:

| Store | Owner | Content |
| --- | --- | --- |
| `settings.json` | `ConfigManager` | Schema version, connection endpoint, UI and log preferences |
| `mapping.json` | `ConfigManager` | Physical control-to-OBS/automation mapping |
| `scripts.json` | `ScriptManager` | Automation name to validated command-list mapping |
| `*.bak` | Respective owner | Last valid recoverable snapshot |
| OS credential entry | `ConfigManager` through keyring | OBS WebSocket password |

Writes replace a temporary file atomically and retain a sanitized valid backup.
Readers merge defaults and may recover a corrupt primary from its backup. Schema
changes require an explicit migration and regression tests; silent destructive
downgrades are not allowed.

## Data flows

### Physical scene or volume action

1. Firmware emits a newline-delimited event.
2. `SerialController` validates and translates it into a typed callback.
3. `StreamDeckApp` resolves the configured mapping.
4. `OBSController` serializes the WebSocket request.
5. OBS events update application state; streaming/recording events also queue LED
   commands back to the firmware.

### Desktop automation

1. Automation text is parsed into typed commands when saved or tested.
2. The repository atomically commits only the canonical command list.
3. A managed worker invokes a restricted PyAutoGUI backend.
4. Cancellation and errors release held keys in a cleanup path.

## Security and trust boundaries

Serial devices, imported profiles, OBS names, and automation text are untrusted
input. Input is bounded and parsed; log output is redacted; secrets are delegated
to the OS; and automation never crosses into Python or shell evaluation. PyAutoGUI
still has the user's desktop privileges, so importing automations requires the same
caution as installing a macro profile.

Release artifacts add another trust boundary. CI produces hashes and supports
Authenticode signing when maintainers configure signing secrets. An unsigned alpha
artifact must be clearly identified as such.

## Evolution rules

- Extend protocol v1 only with ignorable capability tokens or new messages that
  old peers safely reject. Use a new negotiated version for incompatible syntax.
- Keep domain calculations and validation outside widgets so they remain unit
  testable.
- Introduce adapters around third-party libraries instead of exposing their types
  across UI pages.
- Add data migrations before changing persisted shapes.
- Record supported desktop, protocol, firmware, OBS, and hardware combinations in
  every release note.
