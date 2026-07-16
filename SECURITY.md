# Security policy

## Supported versions

Until the first stable release, security fixes are made only on the current
development branch and the most recent pre-release. Historical tags are not
supported. A release-specific support table will replace this statement at 1.0.

## Report a vulnerability privately

Use GitHub's **Security → Report a vulnerability** form for this repository:

<https://github.com/zarmat99/StreamDeck/security/advisories/new>

Do not open a public issue. If private reporting is unavailable, contact the
repository owner privately through the contact method on their GitHub profile and
ask for a secure reporting channel before sending details.

Include the affected version or commit, operating system, impact, reproduction
steps, and any proposed mitigation. Remove OBS passwords, tokens, personal data,
and production logs. An encrypted proof of concept can be arranged after initial
contact.

The maintainers target an acknowledgement within five business days. This is a
best-effort target, not a service-level agreement. Coordinated disclosure timing
will be agreed after impact and remediation are understood.

## Credential exposure

If a real credential reaches Git history, logs, an issue, or an artifact:

1. Revoke or rotate it immediately; deleting the file is not sufficient.
2. Disable affected sessions and review the provider's access logs.
3. Report the exposure privately using the process above.
4. Remove it from the current tree and, after coordination, sanitize history and
   invalidate cached artifacts or forks where possible.
5. Add a regression rule or test without embedding the original value.

The local scanner (`python scripts/scan_secrets.py`) detects several common secret
formats but cannot prove a repository is clean. Repository-host secret scanning
and human review remain necessary.

## Security boundaries

- OBS credentials belong in the OS credential store, not JSON or logs.
- Automation commands can control keyboard and pointer input. Only run profiles
  from trusted sources and stop automations before entering sensitive data.
- Serial input is treated as untrusted and must remain length- and format-checked.
- A release is trusted only when its hash and, where available, Windows signature
  match the release metadata.
