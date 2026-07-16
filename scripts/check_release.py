"""Validate that a release tag and application version agree."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "src" / "version.py"
PROJECT_FILE = ROOT / "pyproject.toml"
REQUIREMENTS_FILE = ROOT / "requirements.txt"
VERSION_PATTERN = re.compile(r'^APP_VERSION\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def application_version() -> str:
    """Read the version without importing GUI dependencies."""

    match = VERSION_PATTERN.search(VERSION_FILE.read_text(encoding="utf-8"))
    if match is None:
        raise SystemExit(f"APP_VERSION was not found in {VERSION_FILE}")
    return match.group(1)


def validate_runtime_requirements() -> None:
    """Keep the compatibility requirements file aligned with package metadata."""

    metadata = tomllib.loads(PROJECT_FILE.read_text(encoding="utf-8"))
    declared = metadata.get("project", {}).get("dependencies", [])
    compatibility = [
        line.strip()
        for line in REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if declared != compatibility:
        raise SystemExit(
            "requirements.txt must mirror project.dependencies in pyproject.toml"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate APP_VERSION and, when supplied, a release tag."
    )
    parser.add_argument(
        "tag",
        nargs="?",
        help=(
            "release tag such as v1.2.3; defaults to RELEASE_TAG or "
            "GITHUB_REF_NAME, otherwise only APP_VERSION is validated"
        ),
    )
    args = parser.parse_args()

    validate_runtime_requirements()
    current = application_version()
    if not SEMVER_PATTERN.fullmatch(current):
        raise SystemExit(f"APP_VERSION is not valid semantic versioning: {current}")

    tag = args.tag or os.environ.get("RELEASE_TAG") or os.environ.get("GITHUB_REF_NAME")
    if tag is None:
        print(f"application version verified: {current} (no release tag supplied)")
        return 0

    tag_version = tag.removeprefix("v")
    if not SEMVER_PATTERN.fullmatch(tag_version):
        raise SystemExit(f"release tag is not valid semantic versioning: {tag}")

    if current != tag_version:
        raise SystemExit(f"release tag {tag} does not match APP_VERSION {current}")
    print(f"release version verified: {current} ({tag})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
