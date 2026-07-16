# -*- mode: python ; coding: utf-8 -*-
"""Repeatable PyInstaller definition for the Windows desktop bundle."""

from pathlib import Path
import re

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)


datas = collect_data_files("customtkinter")
hiddenimports = collect_submodules("keyring.backends")

version_source = Path("src/version.py").read_text(encoding="utf-8")
version_match = re.search(
    r'^APP_VERSION\s*=\s*["\']([^"\']+)["\']', version_source, re.MULTILINE
)
if version_match is None:
    raise RuntimeError("APP_VERSION was not found in src/version.py")
product_version = version_match.group(1)
numeric_version = tuple(
    int(part) for part in product_version.split("-", 1)[0].split(".")
)
if len(numeric_version) != 3:
    raise RuntimeError(f"PyInstaller requires a three-part version: {product_version}")
file_version = (*numeric_version, 0)

version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=file_version, prodvers=file_version),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct("FileDescription", "StreamDeck Control"),
                        StringStruct("FileVersion", product_version),
                        StringStruct("InternalName", "streamdeck-control"),
                        StringStruct(
                            "LegalCopyright",
                            "Copyright 2026 StreamDeck Control contributors",
                        ),
                        StringStruct("OriginalFilename", "StreamDeck Control.exe"),
                        StringStruct("ProductName", "StreamDeck Control"),
                        StringStruct("ProductVersion", product_version),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)

analysis = Analysis(
    ["scripts/pyinstaller_entry.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "mypy", "ruff"],
    noarchive=False,
)
pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="StreamDeck Control",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=version_info,
    uac_admin=False,
)

bundle = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="StreamDeck Control",
)
