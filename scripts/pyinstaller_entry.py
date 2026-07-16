"""Minimal source-tree GUI entry point used by PyInstaller."""

# The wheel maps ``src`` to the public ``streamdeck_control`` package. PyInstaller
# analyzes the checkout directly, so this build-only entry point uses its physical
# package name instead of relying on an editable-install import hook.
from src.app import run


if __name__ == "__main__":
    run()
