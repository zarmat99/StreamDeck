# Changelog

All notable changes to the current product line are documented here. The format is
based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and release
versions are intended to follow [Semantic Versioning](https://semver.org/).

Repository tags created before this changelog are historical development
artifacts; no release notes are reconstructed for them.

## [Unreleased]

### Added

- Installable `streamdeck-control` Python package metadata for Python 3.11–3.13.
- Windows desktop, firmware, and release automation workflows.
- Repeatable PyInstaller definition and guarded local release script.
- Automated tests, coverage configuration, static checks, dependency auditing,
  pre-commit hooks, and a local secret scanner.
- Architecture, protocol, hardware, installation, automation, testing,
  troubleshooting, release, privacy, security, support, and contribution guides.
- GitHub issue forms, pull-request checklist, and Dependabot configuration.

### Security

- Documented private vulnerability reporting and credential-rotation procedures.
- Release signing can be enabled with repository secrets; no signing credentials
  are stored in this repository.

## Release note requirements

Each future release entry must identify user-visible changes, configuration or
protocol migrations, supported desktop/firmware combinations, known limitations,
and security-relevant fixes. Dates use `YYYY-MM-DD`.
