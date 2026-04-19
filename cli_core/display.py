"""
Display utilities: progress bars, spinners, formatting helpers.
By EleRiSey Studio — github.com/yorikelesey-dot
discord.gg/RcKBmrn2rj
"""

import time
import threading
import sys
import os
from typing import Optional
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich.progress import (
    Progress, SpinnerColumn, BarColumn, TextColumn,
    DownloadColumn, TransferSpeedColumn, TimeRemainingColumn,
    TaskProgressColumn, MofNCompleteColumn
)
from rich.live import Live
from rich.align import Align
from rich import box

from .styles import Colors, Icons, SPINNER_DOTS, PROGRESS_FILL, PROGRESS_EMPTY

# ── Rich Console ────────────────────────────────────────
# On Windows: force terminal mode so Rich uses ANSI instead of the
# Win32 API path, which cannot handle UTF-8 box-drawing characters.
_FORCE_TERMINAL = sys.platform == "win32"
console = Console(
    force_terminal=_FORCE_TERMINAL,
    force_jupyter=False,
    markup=True,
    highlight=False,
    emoji=True,
)


def make_progress() -> Progress:
    """Returns a styled Rich Progress bar for downloads."""
    return Progress(
        SpinnerColumn(spinner_name="dots", style=f"bold {Colors.CYAN}"),
        TextColumn("[bold {task.fields[color]}]{task.description}[/]", justify="left"),
        BarColumn(
            bar_width=38,
            style=Colors.DIM,
            complete_style=Colors.GREEN,
            finished_style=Colors.GREEN,
        ),
        TaskProgressColumn(style=f"bold {Colors.YELLOW}"),
        DownloadColumn(binary_units=True),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
        expand=False,
    )


def format_size(bytes_: Optional[int]) -> str:
    """Format bytes as a human-readable size string."""
    if not bytes_:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"


def format_duration(seconds: Optional[int]) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    if not seconds:
        return "?"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_views(views: Optional[int]) -> str:
    """Format view/like count (1.2M, 345K, etc.)."""
    if not views:
        return "?"
    if views >= 1_000_000_000:
        return f"{views / 1e9:.1f}B"
    if views >= 1_000_000:
        return f"{views / 1e6:.1f}M"
    if views >= 1_000:
        return f"{views / 1e3:.1f}K"
    return str(views)


def color_for_percent(pct: float) -> str:
    """Returns a color based on download progress percentage."""
    if pct < 25:
        return Colors.RED
    elif pct < 75:
        return Colors.YELLOW
    return Colors.GREEN


def draw_ascii_progress(pct: float, width: int = 40) -> str:
    """Render a colored ASCII progress bar string."""
    filled = int(width * pct / 100)
    empty  = width - filled
    color  = color_for_percent(pct)
    return f"[{color}]{PROGRESS_FILL * filled}[/][dim]{PROGRESS_EMPTY * empty}[/]"


def spin_once(frame_idx: int) -> str:
    """Return one spinner frame."""
    return SPINNER_DOTS[frame_idx % len(SPINNER_DOTS)]


def print_header(text: str, subtitle: str = "") -> None:
    """Print a styled section header panel."""
    console.print()
    console.print(Panel(
        Align.center(
            f"[bold {Colors.CYAN}]{text}[/]\n[dim]{subtitle}[/]"
            if subtitle else f"[bold {Colors.CYAN}]{text}[/]"
        ),
        border_style=Colors.BLUE,
        box=box.DOUBLE_EDGE,
        padding=(0, 2),
    ))


def print_success(msg: str) -> None:
    console.print(f"\n  [{Colors.GREEN}]{Icons.CHECK} {msg}[/]")


def print_error(msg: str) -> None:
    console.print(f"\n  [{Colors.RED}]{Icons.CROSS} {msg}[/]")


def print_warning(msg: str) -> None:
    console.print(f"\n  [{Colors.WARNING}]{Icons.WARNING}  {msg}[/]")


def print_info(msg: str) -> None:
    console.print(f"  [{Colors.INFO}]{Icons.INFO}  {msg}[/]")


def hr(char: str = "─", color: str = Colors.BG_BORDER) -> None:
    """Print a full-width horizontal rule."""
    width = console.width or 80
    console.print(f"[{color}]{char * width}[/]")
