# Privacy notice

Last updated: 2026-07-10

## Summary

The current StreamDeck Control application contains no analytics, advertising,
crash-report upload, account system, cloud synchronization, or automatic telemetry.
It does not intentionally transmit usage information to the project maintainers.

## Data handled locally

- Connection settings, mappings, UI preferences, and automations are stored in the
  current user's application-data directory.
- The OBS WebSocket password is requested from and written to the operating-system
  credential store through `keyring`. It is not intentionally persisted in JSON.
- Rotating diagnostic logs may contain device ports, host names, OBS object names,
  error details, and user-triggered operations. Password-like values are redacted,
  but logs should still be reviewed before sharing.
- Declarative automations are stored locally and can generate keyboard and pointer
  input through PyAutoGUI.

Atomic configuration backups use the `.bak` suffix beside their primary files and
therefore have the same sensitivity and retention expectations.

## Connections

The application connects only to the OBS WebSocket endpoint configured by the user
and to the selected local serial device. `localhost` is the default, but entering a
remote OBS host sends WebSocket traffic to that host. The application does not
control the remote server's logging or retention.

Installing dependencies, cloning the repository, using GitHub, checking for
dependency vulnerabilities, and building PlatformIO firmware involve those tools
and their own providers; their privacy terms are separate from the application.

## User control and deletion

Users can remove application JSON files and logs from the per-user data directory
and delete the `streamdeck-controller` / `obs-websocket` credential from the OS
credential manager. Close the application first. See
[troubleshooting](docs/troubleshooting.md#reset-local-state) for a safe reset.

The project maintainers do not receive these local files unless a user chooses to
share them in a support or security report. Shared material is retained by the
chosen collaboration platform according to its policies.

Any future telemetry, updater, cloud feature, or remote crash reporting must be
opt-in, documented before release, minimized, and accompanied by an updated notice.
