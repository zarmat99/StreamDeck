# Declarative automations

Automation profiles contain a name and a list of validated commands. The engine
does not evaluate Python, import modules, interpolate environment variables, or
start a shell. It can still control keyboard and pointer input with the current
user's privileges, so only use automations you have reviewed.

## Commands

| Syntax | Effect |
| --- | --- |
| `press <key>` | Press and release one key |
| `hold <key>` | Hold one key until `release` or cleanup |
| `release <key>` | Release one held key |
| `combo ctrl+shift+s` | Hold the listed keys in order and release them safely |
| `write some text` | Type the text after the first space |
| `delay 0.25` | Wait for seconds; range is 0 through 3600 |
| `move 400,300` | Move pointer to absolute screen coordinates |
| `click left` | Click at the current position |
| `click right,400,300` | Click the selected button at coordinates |

Blank lines and lines whose first non-space character is `#` are ignored. Key names
are normalized to lowercase and cannot contain whitespace, `+`, or `$`. A script is
limited to 1,000 commands and `write` text to 10,000 characters.

Example:

```text
# Open a save dialog and type a deterministic file name.
combo ctrl+shift+s
delay 0.25
write rehearsal-scene
press enter
```

The historical `$` combo separator is accepted for migration, but new profiles
should use `+`. Saved commands are canonicalized.

## Execution and cancellation

Only one instance of a named automation runs at a time. Test executions use their
own managed identifier. Cancellation is cooperative between commands; a long
PyAutoGUI operation may not stop at the exact instant requested. Cleanup attempts
to release every key held by the automation, including after an error.

PyAutoGUI's platform fail-safe remains relevant. Keep a reliable way to regain
control and test pointer actions with non-sensitive applications first. Do not run
automations while entering passwords, approving payments, or using an elevated
desktop.

## Storage and sharing

The application stores a JSON object mapping names to command-string lists in
`scripts.json`, with an atomic `.bak` snapshot. Do not hand-edit it while the
application is running. Examples belong under `examples/` and must use synthetic
names and data.

Before importing a profile:

1. Read every command and check all coordinates against the target display layout.
2. Remove unexpected `write`, pointer, or long-delay actions.
3. Test with OBS disconnected and an inert application focused.
4. Bind it to G0–G3 only after the test completes and cancellation works.

Automation profiles are data, not plug-ins. Proposals to add shell, URL download,
PowerShell, Python, or executable-launch commands require a separate security
design and are outside protocol v1.
