# Contributing

Thank you for helping improve StreamDeck Control. The project is in an alpha phase,
so small, reviewable changes with tests and migration notes are preferred.

## Before starting

1. Search existing issues and pull requests.
2. Open an issue before a large UI, protocol, dependency, hardware, or data-format
   change so the compatibility impact can be agreed first.
3. Never post a vulnerability or real credential publicly; use the process in
   [SECURITY.md](SECURITY.md).

## Development setup

Use a supported CPython version on Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
pre-commit install --hook-type pre-commit --hook-type pre-push
```

Run the desktop and firmware verification described in [docs/testing.md](docs/testing.md).
No attached OBS instance or hardware should be required by unit tests.

## Change requirements

- Keep Tk widget access on the Tk main thread.
- Give each external transport exactly one lifecycle owner; reconnect code must not
  accumulate workers.
- Preserve atomic configuration writes, backups, schema versions, and credential
  redaction.
- Treat protocol changes as compatibility changes and update both firmware and
  [docs/protocol.md](docs/protocol.md).
- Use declarative automation commands only. Do not introduce `eval`, `exec`, shell
  execution, or unvalidated Python automation.
- Add or update tests for behavior and failure paths.
- Update user documentation and `CHANGELOG.md` for visible changes.
- Do not commit generated firmware, executables, local configuration, logs, IDE
  settings, or credentials.

## Verification

```powershell
python scripts/scan_secrets.py
python scripts/check_release.py
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest --cov=src --cov-report=term-missing --cov-report=xml
pio run -d firmware -e uno_active_high
pio run -d firmware -e uno_internal_pullup
python -m pip_audit --strict --requirement requirements.txt
python -m build --no-isolation
python -m twine check dist/*
python -m PyInstaller --clean --noconfirm streamdeck_control.spec
python scripts/check_pyinstaller.py
```

The pull request must explain any check that cannot be run locally. CI is required
to pass before merge.

## Commits and pull requests

Write focused commits in imperative form. Conventional prefixes such as `fix:`,
`feat:`, `test:`, `docs:`, and `build:` are encouraged. Do not rewrite unrelated
work. Complete the pull-request template, include before/after screenshots for UI
changes, and identify the hardware profile used for device tests.

## Contribution rights

The repository currently uses a temporary all-rights-reserved license. By
submitting a contribution, you represent that you have the right to submit it and
grant the project copyright holders a perpetual, worldwide, non-exclusive,
royalty-free right to use, reproduce, modify, redistribute, and relicense that
contribution as part of this project. Your submission does not itself change the
license of the repository. A separate contributor agreement may be requested
before accepting substantial contributions.

If these terms are not acceptable, do not submit code; use an issue to discuss the
proposal instead. This policy is not legal advice and should be reviewed together
with the definitive project license.
