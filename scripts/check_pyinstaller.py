"""Reject incomplete PyInstaller output that would fail at application startup."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WARNING_FILE = ROOT / "build" / "streamdeck_control" / "warn-streamdeck_control.txt"
BUNDLE_DIR = ROOT / "dist" / "StreamDeck Control"
EXECUTABLE = BUNDLE_DIR / "StreamDeck Control.exe"
CUSTOMTKINTER_ASSETS = BUNDLE_DIR / "_internal" / "customtkinter" / "assets"
CRITICAL_WARNING_FRAGMENTS = (
    "missing module named tkinter ",
    "missing module named 'tkinter.",
    "missing module named _tkinter ",
    "missing module named src ",
    "missing module named streamdeck_control ",
)


def main() -> int:
    """Validate files and critical import warnings from the latest bundle."""

    required = (WARNING_FILE, EXECUTABLE, CUSTOMTKINTER_ASSETS)
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"PyInstaller output is incomplete: {', '.join(missing)}")

    warnings = WARNING_FILE.read_text(encoding="utf-8", errors="replace")
    critical = [
        fragment.strip()
        for fragment in CRITICAL_WARNING_FRAGMENTS
        if fragment in warnings
    ]
    if critical:
        raise SystemExit(
            "PyInstaller omitted startup dependencies: " + ", ".join(critical)
        )

    print("PyInstaller bundle structure and startup imports verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
