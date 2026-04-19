# -*- mode: python ; coding: utf-8 -*-
# RebornYoutubeDowloader — PyInstaller spec
# By EleRiSey Studio — github.com/yorikelesey-dot

import sys
from pathlib import Path

# yt-dlp helper modules that must be explicitly included
YT_DLP_HIDDENIMPORTS = [
    "yt_dlp", "yt_dlp.extractor", "yt_dlp.extractor._extractors",
    "yt_dlp.postprocessor", "yt_dlp.downloader",
    "yt_dlp.utils", "yt_dlp.networking",
    "yt_dlp.networking._urllib", "yt_dlp.networking.common",
]

RICH_HIDDENIMPORTS = [
    "rich", "rich.console", "rich.panel", "rich.table", "rich.text",
    "rich.align", "rich.live", "rich.progress", "rich.prompt",
    "rich.markup", "rich.columns", "rich.rule", "rich.padding",
    "rich.box", "rich.style", "rich.theme", "rich.spinner",
    "rich.ansi", "rich.segment", "rich.measure", "rich.cells",
    "rich._ratio", "rich.columns", "rich.highlighter",
]

block_cipher = None

a = Analysis(
    ["cli.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=YT_DLP_HIDDENIMPORTS + RICH_HIDDENIMPORTS + [
        "certifi", "urllib3", "websockets", "mutagen",
        "brotli", "pycryptodomex", "Crypto",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "matplotlib", "numpy", "pandas",
        "scipy", "PIL", "cv2", "torch",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="RebornYoutubeDowloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,           # compress — smaller .exe
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,       # it's a CLI tool — keep the terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="icon.ico",  # uncomment and add icon.ico if you have one
)
