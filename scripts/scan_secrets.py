"""Small dependency-free scanner for common committed credential formats.

This is a fast local guardrail, not a replacement for a managed secret scanner.
Only file names, line numbers and finding categories are printed so an accidental
secret is not copied into CI logs.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 2 * 1024 * 1024
SKIPPED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pio",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "htmlcov",
    "logs",
    "__pycache__",
}
SKIPPED_SUFFIXES = {
    ".bin",
    ".dll",
    ".elf",
    ".exe",
    ".gif",
    ".hex",
    ".ico",
    ".jpg",
    ".jpeg",
    ".pdf",
    ".png",
    ".pyc",
    ".pyd",
    ".so",
    ".zip",
}
PLACEHOLDERS = {
    "",
    "changeme",
    "example",
    "none",
    "not-a-secret",
    "placeholder",
    "redacted",
    "secret",
    "test",
    "your-password",
}


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]
    value_group: int | None = None


RULES = (
    Rule(
        "private key",
        re.compile("-----BEGIN " + r"(?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    Rule("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b")),
    Rule("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}\b")),
    Rule("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    Rule(
        "assigned credential",
        re.compile(
            r"(?i)\b(?:api[_-]?key|client[_-]?secret|password|passwd|token)\b"
            r"\s*[:=]\s*[\"']([^\"'\r\n]{8,})[\"']"
        ),
        1,
    ),
)


def candidate_paths(explicit_paths: Iterable[str]) -> list[Path]:
    paths = list(explicit_paths)
    if not paths:
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        paths = [item for item in result.stdout.decode().split("\0") if item]

    candidates: list[Path] = []
    for value in paths:
        path = Path(value)
        if not path.is_absolute():
            path = ROOT / path
        try:
            relative = path.resolve().relative_to(ROOT.resolve())
        except ValueError:
            continue
        if any(part in SKIPPED_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() in SKIPPED_SUFFIXES or not path.is_file():
            continue
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        candidates.append(path)
    return candidates


def is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in PLACEHOLDERS or normalized.startswith(("${", "{{", "<"))


def scan_file(path: Path) -> list[tuple[int, str]]:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return []

    findings: list[tuple[int, str]] = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        for rule in RULES:
            match = rule.pattern.search(line)
            if match is None:
                continue
            if rule.value_group is not None and is_placeholder(
                match.group(rule.value_group)
            ):
                continue
            findings.append((line_number, rule.name))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="optional paths to scan")
    args = parser.parse_args()

    total = 0
    for path in candidate_paths(args.paths):
        for line_number, category in scan_file(path):
            relative = path.resolve().relative_to(ROOT.resolve())
            print(f"{relative}:{line_number}: possible {category}", file=sys.stderr)
            total += 1
    if total:
        print(
            f"secret scan failed with {total} finding(s); rotate real leaked credentials",
            file=sys.stderr,
        )
        return 1
    print("secret scan passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
