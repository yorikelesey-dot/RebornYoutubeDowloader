#!/usr/bin/env python3
"""
RebornYoutubeSaver CLI v2.0
Красивый загрузчик YouTube видео/аудио
"""

import sys
import os
import io

# ── Fix Windows console encoding ──────────────────────────────
if sys.platform == "win32":
    # Enable UTF-8 output on Windows
    try:
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace"
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace"
        )
    except AttributeError:
        pass  # Already wrapped
    # Enable ANSI escape codes in cmd/powershell
    os.system("")
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32  # type: ignore
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

# Also set environment variable for subprocesses
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli_core.app import RebornApp

if __name__ == "__main__":
    app = RebornApp()
    app.run()
