# Release process

Releases are maintainer operations from a clean, protected branch. A tag is not a
release until quality evidence, hashes, compatibility notes, and artifact signing
status are published together.

## One-time repository setup

- Protect the release branch and require desktop and firmware workflows.
- Enable private vulnerability reporting, dependency review, and hosted secret
  scanning where available.
- Create a GitHub Environment named `release` with required reviewers.
- Obtain an organization-controlled Authenticode certificate and document custody,
  renewal, revocation, and incident procedures.
- Store the PFX as base64 in `WINDOWS_SIGNING_CERTIFICATE_BASE64` and its password
  in `WINDOWS_SIGNING_CERTIFICATE_PASSWORD` environment secrets. Never put either
  value in a workflow, variable, issue, artifact, or local repository file.

The workflow builds unsigned artifacts when the signing secrets are absent and
labels that fact in its provenance text. Such artifacts are alpha/test artifacts,
not signed production releases.

## Release gates

1. Confirm product name, temporary/proposed license, third-party notices, and
   distribution rights with qualified legal review.
2. Select the supported Windows, OBS, desktop, protocol, firmware, and hardware
   matrix and complete manual/soak evidence from [testing.md](testing.md).
3. Resolve critical/high vulnerabilities or document an approved, time-bounded
   exception. Rotate any exposed credential before continuing.
4. Update `APP_VERSION` in `src/version.py` using semantic versioning.
5. Move relevant `CHANGELOG.md` items into a dated version section and document
   migrations, breaking changes, signing status, and known limitations.
6. Verify examples contain synthetic data and privacy/security documents remain
   accurate.

## Local candidate

```powershell
git status --short
.\scripts\build_release.ps1 -ReleaseTag v3.0.0
```

Replace the example version. The script rejects a dirty worktree by default,
checks version/dependency metadata, runs the desktop gates and runtime audit,
builds both firmware profiles, and creates Python and PyInstaller artifacts.
`-AllowDirty` exists only for local diagnostics and must not be used to produce a
published candidate. Build output remains ignored. Test the PyInstaller directory
on a clean standard-user Windows environment.

## Tag and automated build

Create a signed or verified maintainer tag after the release commit is reviewed:

```powershell
git tag -s v0.1.0 -m "StreamDeck Control 0.1.0"
git push origin v0.1.0
```

The tag must exactly match `APP_VERSION`. The release workflow:

1. checks out the tag and validates the version;
2. repeats desktop tests, coverage, audit, package build, and PyInstaller build;
3. signs all shipped `.exe` files only when both signing secrets are available;
4. creates a versioned ZIP, Python distributions, firmware HEX files, a signing
   status file, the resolved build environment, source commit, and
   `SHA256SUMS.txt`;
5. uploads immutable workflow artifacts and creates a draft GitHub release.

Maintainers review the draft, download and verify hashes/signatures, run final
smoke tests, attach compatibility/release notes, and only then publish it. Do not
replace files beneath an existing release; issue a new patch version.

## Signature verification

On a signed candidate:

```powershell
Get-AuthenticodeSignature ".\StreamDeck Control.exe" | Format-List
```

The status must be `Valid`, the certificate subject must match the approved
publisher, and a trusted timestamp should remain valid after certificate expiry.
Record the certificate thumbprint in private release evidence and the publisher
name in public notes; do not publish private-key material or the PFX.

## Post-release

- Install from the public ZIP on a clean account and repeat one OBS/device smoke
  test using non-production credentials.
- Verify the release page hashes, signature statement, firmware artifacts, and
  source tag.
- Monitor support and security channels and record regressions in the changelog.
- Preserve release evidence and reproducible inputs according to the project's
  retention policy.

If a release is unsafe, mark it affected immediately, remove it from recommended
downloads without silently rewriting artifacts, publish mitigation, rotate or
revoke credentials/certificates if implicated, and release a corrected version.
