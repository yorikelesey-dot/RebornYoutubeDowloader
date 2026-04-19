"""
RebornYoutubeSaver CLI — Main Application.
Fully interactive CLI with Rich animations.

By EleRiSey Studio — github.com/EleRiSey
"""

import os
import sys
import re
import time
import threading
from typing import Optional, List, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.live import Live
from rich.columns import Columns
from rich.rule import Rule
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import (
    Progress, SpinnerColumn, BarColumn, TextColumn,
    DownloadColumn, TransferSpeedColumn, TimeRemainingColumn,
    TaskProgressColumn,
)
from rich import box
from rich.padding import Padding
from rich.markup import escape

from .styles import (
    Colors, Icons, LOGO, LOGO_SUBTITLE, LOGO_FOOTER,
    SPINNER_DOTS, STUDIO_NAME, APP_VERSION, STUDIO_GITHUB, STUDIO_DISCORD,
)
from .display import (
    console, format_size, format_duration, format_views,
    draw_ascii_progress, color_for_percent,
    print_success, print_error, print_warning, print_info, hr,
)
from .config import config
from .history import history
from .downloader import (
    get_video_info, get_available_formats,
    download_video, get_playlist_info,
    DownloadInfo,
)
from .bypass import inter_download_sleep, session_stats

# ─────────────────── URL PATTERN ───────────────────
YT_PATTERN = re.compile(
    r"(https?://(?:www\.|m\.)?(?:youtube\.com|youtu\.be|youtube-nocookie\.com)"
    r"(?:/shorts/|/watch\?v=|/v/|/playlist\?|/)[\w\-?=&%#@.]+)",
    re.IGNORECASE,
)


def is_youtube_url(text: str) -> bool:
    return bool(YT_PATTERN.search(text.strip()))


# ─────────────────── SPLASH SCREEN ───────────────────

def show_splash():
    """Show animated splash screen."""
    console.clear()
    console.print()
    console.print(Align.center(LOGO))
    console.print(Align.center(LOGO_SUBTITLE))
    console.print(Align.center(LOGO_FOOTER))
    console.print()

    # Animated loading bar
    frames = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"] * 5
    width  = 40
    with Live(console=console, refresh_per_second=30) as live:
        for i in range(len(frames)):
            filled  = int(width * i / (len(frames) - 1))
            bar_str = f"[{Colors.CYAN}]{'█' * filled}[/][dim]{'░' * (width - filled)}[/]"
            percent = int(100 * i / (len(frames) - 1))
            live.update(
                Align.center(
                    Text.from_markup(f"{bar_str}  [{Colors.YELLOW}]{percent}%[/]")
                )
            )
            time.sleep(0.015)

    console.print()
    _print_divider()


# ─────────────────── HELPERS ───────────────────

def _print_divider(char: str = "─") -> None:
    w = min(console.width or 80, 80)
    console.print(Align.center(f"[{Colors.BG_BORDER}]{char * w}[/]"))


def _panel(content, title: str = "", color: str = Colors.BLUE) -> Panel:
    return Panel(
        content,
        title=f"[bold {color}]{title}[/]" if title else None,
        border_style=color,
        box=box.ROUNDED,
        padding=(0, 1),
    )


def _fmt_row(label: str, value: str, color: str = Colors.WHITE) -> str:
    return f"  [{Colors.DIM}]{label:<16}[/][{color}]{value}[/]"


# ─────────────────── VIDEO INFO PANEL ───────────────────

def show_video_info(info: Dict[str, Any]) -> None:
    """Render a rich panel with video metadata."""
    title     = str(info.get("title") or "Unknown")
    uploader  = str(info.get("uploader") or info.get("channel") or "?")
    duration  = format_duration(info.get("duration"))
    views     = format_views(info.get("view_count"))
    likes     = format_views(info.get("like_count"))
    upload_dt = str(info.get("upload_date") or "")
    if upload_dt and len(upload_dt) == 8:
        upload_dt = f"{upload_dt[6:8]}.{upload_dt[4:6]}.{upload_dt[:4]}"

    raw_desc    = str(info.get("description") or "")
    description = raw_desc[:120] + ("…" if len(raw_desc) > 120 else "")

    lines = [
        f"[bold {Colors.WHITE}]{escape(title)}[/]",
        "",
        _fmt_row(f"{Icons.CHANNEL} Channel",  escape(uploader), Colors.CYAN),
        _fmt_row(f"{Icons.ETA} Duration",     duration,         Colors.YELLOW),
        _fmt_row(f"{Icons.VIEWS} Views",      views,            Colors.GREEN),
    ]
    if likes != "?":
        lines.append(_fmt_row(f"{Icons.LIKES} Likes", likes, Colors.RED))
    if upload_dt:
        lines.append(_fmt_row("📅 Uploaded", upload_dt, Colors.DIM))
    if description:
        lines += ["", f"  [{Colors.DIM}]{escape(description)}[/]"]

    console.print()
    console.print(_panel("\n".join(lines), f"{Icons.VIDEO} Video found", Colors.CYAN))


# ─────────────────── FORMAT SELECTION ───────────────────

def show_format_menu(formats: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Interactive format picker. Returns chosen format or None on cancel."""
    console.print()
    table = Table(
        title=f"[bold {Colors.YELLOW}]{Icons.QUALITY} Select Quality[/]",
        box=box.ROUNDED,
        border_style=Colors.BLUE,
        header_style=f"bold {Colors.CYAN}",
        show_lines=False,
        expand=False,
        min_width=58,
    )
    table.add_column("#",       style=f"bold {Colors.YELLOW}", width=4,  justify="right")
    table.add_column("Format",  style=f"bold {Colors.WHITE}",  width=30)
    table.add_column("Size",    style=Colors.GREEN,             width=10, justify="right")
    table.add_column("Type",    style=Colors.DIM,               width=10)

    type_colors = {
        "best":      Colors.YELLOW,
        "video":     Colors.CYAN,
        "audio":     Colors.GREEN,
        "audio_mp3": Colors.MAGENTA,
    }
    type_labels = {
        "best":      "⭐ auto",
        "video":     "🎬 video",
        "audio":     "🎵 audio",
        "audio_mp3": "🎶 mp3",
    }

    for i, fmt in enumerate(formats, 1):
        size_str   = format_size(fmt.get("filesize")) if fmt.get("filesize") else "[dim]~auto[/]"
        fmt_type   = fmt.get("type", "?")
        type_color = type_colors.get(fmt_type, Colors.DIM)
        type_label = type_labels.get(fmt_type, fmt_type)

        table.add_row(
            str(i),
            fmt["label"],
            size_str,
            f"[{type_color}]{type_label}[/]",
        )

    cancel_idx = len(formats) + 1
    table.add_row(str(cancel_idx), f"[{Colors.RED}]{Icons.CANCEL} Cancel[/]", "", "")

    console.print(table)
    console.print()

    while True:
        try:
            choice = IntPrompt.ask(
                f"  [{Colors.YELLOW}]{Icons.ARROW} Enter number[/]",
                console=console,
            )
            if choice == cancel_idx:
                return None
            if 1 <= choice <= len(formats):
                return formats[choice - 1]
            print_warning(f"Enter a number from 1 to {cancel_idx}")
        except (KeyboardInterrupt, EOFError):
            return None


# ─────────────────── DOWNLOAD PROGRESS ───────────────────

def run_download(
    url: str,
    fmt: Dict[str, Any],
    info: Dict[str, Any],
) -> Optional[str]:
    """Launch download with animated progress bar. Returns file path or None."""
    cfg     = config.to_ydl_cfg
    out_dir = config.ensure_download_dir()

    dl_info    = DownloadInfo()
    result_path: list = [None]
    done_event = threading.Event()

    def on_progress(d: DownloadInfo):
        for slot in d.__slots__:
            setattr(dl_info, slot, getattr(d, slot))
        if d.status in ("done", "error"):
            done_event.set()

    dl_thread = threading.Thread(
        target=_download_thread,
        args=(url, fmt, out_dir, cfg, on_progress, result_path),
        daemon=True,
    )

    console.print()

    with Progress(
        SpinnerColumn(spinner_name="dots2", style=f"bold {Colors.CYAN}"),
        TextColumn("[bold {task.fields[stage_color]}]{task.fields[stage]}"),
        BarColumn(
            bar_width=36,
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
        refresh_per_second=10,
    ) as progress:

        task = progress.add_task(
            "",
            total=100,
            stage="⏳ Preparing…",
            stage_color=Colors.YELLOW,
        )

        dl_thread.start()

        while not done_event.is_set():
            time.sleep(0.1)
            status = dl_info.status
            pct    = dl_info.percent

            if status == "downloading":
                total = dl_info.total
                if total:
                    progress.update(task, total=total, completed=dl_info.downloaded)
                else:
                    progress.update(task, total=100, completed=pct)

                stage_color = color_for_percent(pct)
                frag_note   = ""
                if dl_info.fragment_count > 1:
                    frag_note = f" [{dl_info.fragment_idx}/{dl_info.fragment_count} frags]"

                progress.update(task,
                    stage=f"{Icons.DOWNLOAD} Downloading{frag_note}",
                    stage_color=stage_color,
                )

            elif status == "ratelimited":
                from .bypass import session as _bs
                left     = _bs.backoff_remaining
                left_str = f" ({left:.0f}s)" if left > 0 else ""
                atm      = dl_info.attempt
                progress.update(task,
                    total=100, completed=0,
                    stage=f"⏳ Rate limited{left_str} [attempt {atm}]",
                    stage_color=Colors.WARNING,
                )

            elif status == "retry":
                atm = dl_info.attempt
                progress.update(task,
                    stage=f"🔄 Retry {atm} — switching client…",
                    stage_color=Colors.YELLOW,
                )

            elif status == "merging":
                progress.update(task,
                    total=100, completed=100,
                    stage=f"{Icons.SETTINGS} Merging streams…",
                    stage_color=Colors.MAGENTA,
                )

            elif status == "processing":
                progress.update(task,
                    total=100, completed=100,
                    stage=f"{Icons.SETTINGS} Converting…",
                    stage_color=Colors.MAGENTA,
                )

            elif status == "error":
                progress.update(task,
                    stage=f"{Icons.CROSS} Failed!",
                    stage_color=Colors.RED,
                )
                break

            elif status == "done":
                progress.update(task,
                    total=100, completed=100,
                    stage=f"{Icons.CHECK} Done!",
                    stage_color=Colors.GREEN,
                )
                break

        done_event.wait(timeout=600)
        dl_thread.join(timeout=5)

    if dl_info.status == "error":
        print_error("Download failed!")
        return None

    return result_path[0]


def _download_thread(url, fmt, out_dir, cfg, on_progress, result_path):
    path = download_video(url, fmt, out_dir, cfg, on_progress=on_progress)
    result_path[0] = path


# ─────────────────── SUCCESS PANEL ───────────────────

def show_success_panel(filepath: str, info: Dict[str, Any], fmt: Dict[str, Any]):
    """Shows a success panel after download completes."""
    filename = os.path.basename(filepath)
    filesize = format_size(os.path.getsize(filepath)) if os.path.exists(filepath) else "?"
    title    = str(info.get("title") or "?")

    lines = [
        f"  [{Colors.GREEN}]{Icons.DONE} File downloaded successfully![/]",
        "",
        _fmt_row(f"{Icons.VIDEO} Title",   escape(title[:50]),    Colors.WHITE),
        _fmt_row(f"{Icons.QUALITY} Format", fmt["label"],          Colors.CYAN),
        _fmt_row(f"{Icons.SIZE} Size",     filesize,               Colors.YELLOW),
        _fmt_row(f"{Icons.FOLDER} File",   escape(filename[:50]), Colors.GREEN),
    ]
    console.print()
    console.print(_panel("\n".join(lines), f"{Icons.ROCKET} Complete", Colors.GREEN))

    if config.get("auto_open_folder"):
        folder = os.path.dirname(os.path.abspath(filepath))
        if sys.platform == "win32":
            os.startfile(folder)


# ─────────────────── HISTORY SCREEN ───────────────────

def show_history():
    """Download history screen."""
    console.clear()
    console.print()
    entries = history.get_recent(30)

    if not entries:
        console.print(_panel(
            Align.center(f"[{Colors.DIM}]History is empty[/]"),
            "📋 Download History",
            Colors.BLUE,
        ))
        Prompt.ask("\n  Press Enter to go back")
        return

    table = Table(
        title=f"[bold {Colors.CYAN}]📋 Download History (last {len(entries)})[/]",
        box=box.ROUNDED,
        border_style=Colors.BLUE,
        header_style=f"bold {Colors.CYAN}",
        show_lines=True,
        expand=True,
    )
    table.add_column("Date",    width=11, style=Colors.DIM)
    table.add_column("Title",   overflow="fold")
    table.add_column("Format",  width=18, style=Colors.CYAN)
    table.add_column("Size",    width=9,  justify="right", style=Colors.GREEN)
    table.add_column("✓",       width=3,  justify="center")

    for e in entries:
        ts    = e.timestamp[:10] if e.timestamp else "?"
        title = (e.title or "?")[:55]
        fmt   = (e.format or "?")[:18]
        size  = format_size(e.filesize) if e.filesize else "?"
        ok    = f"[{Colors.GREEN}]✓[/]" if e.success else f"[{Colors.RED}]✗[/]"
        table.add_row(ts, escape(title), escape(fmt), size, ok)

    console.print(table)
    console.print(f"  [{Colors.DIM}]1. Clear history   2. Back[/]")

    choice = Prompt.ask("\n  Choice", default="2")
    if choice == "1":
        if Confirm.ask(f"  [{Colors.RED}]Clear all history?[/]"):
            history.clear()
            print_success("History cleared.")
            time.sleep(1)


# ─────────────────── SETTINGS SCREEN ───────────────────

_SETTINGS_ITEMS = [
    ("download_dir",             "Download folder",                   "str"),
    ("concurrent_fragments",     "Parallel fragments",                "int"),
    ("rate_limit",               "Speed limit (bytes/s, 0=unlimited)", "int"),
    ("default_quality",          "Default quality",                   "str"),
    ("subtitles",                "Download subtitles",                "bool"),
    ("embed_thumbnail",          "Embed thumbnail",                   "bool"),
    ("geo_bypass",               "Geo-bypass",                        "bool"),
    ("sponsorblock",             "SponsorBlock",                      "bool"),
    ("proxy",                    "Proxy (http://...)",                "str"),
    ("cookies_path",             "Cookies file path",                 "str"),
    ("cookies_browser",          "Browser cookies source",            "str"),
    ("auto_open_folder",         "Open folder after download",        "bool"),
    ("confirm_before_download",  "Confirm before download",           "bool"),
    ("history_limit",            "History limit",                     "int"),
]


def show_settings():
    """Settings screen."""
    while True:
        console.clear()
        console.print()

        table = Table(
            title=f"[bold {Colors.CYAN}]{Icons.SETTINGS} Settings[/]",
            box=box.ROUNDED,
            border_style=Colors.BLUE,
            header_style=f"bold {Colors.CYAN}",
            show_lines=False,
            expand=False,
            min_width=64,
        )
        table.add_column("#",       width=4, justify="right", style=f"bold {Colors.YELLOW}")
        table.add_column("Setting", width=32)
        table.add_column("Value",   style=Colors.GREEN)

        for i, (key, label, _) in enumerate(_SETTINGS_ITEMS, 1):
            val = config.get(key)
            if isinstance(val, bool):
                val_str = f"[{Colors.GREEN}]✓ yes[/]" if val else f"[{Colors.RED}]✗ no[/]"
            else:
                val_str = str(val) if val else f"[{Colors.DIM}]—[/]"
            table.add_row(str(i), label, val_str)

        back_idx  = len(_SETTINGS_ITEMS) + 1
        reset_idx = len(_SETTINGS_ITEMS) + 2
        table.add_row(str(back_idx),  f"[{Colors.CYAN}]◀ Back[/]",        "")
        table.add_row(str(reset_idx), f"[{Colors.RED}]⚠ Reset all[/]",    "")

        console.print(table)
        console.print()

        try:
            choice = IntPrompt.ask(
                f"  [{Colors.YELLOW}]Select setting to change[/]",
                console=console,
            )
        except (KeyboardInterrupt, EOFError):
            break

        if choice == back_idx:
            break
        elif choice == reset_idx:
            if Confirm.ask(f"  [{Colors.RED}]Reset ALL settings to defaults?[/]"):
                config.reset()
                print_success("Settings reset to defaults.")
                time.sleep(1)
        elif 1 <= choice <= len(_SETTINGS_ITEMS):
            key, label, vtype = _SETTINGS_ITEMS[choice - 1]
            cur = config.get(key)
            try:
                if vtype == "bool":
                    new_val = Confirm.ask(f"  {label}", default=bool(cur))
                elif vtype == "int":
                    new_val = IntPrompt.ask(f"  {label}", default=int(cur) if cur else 0, console=console)
                else:
                    new_val = Prompt.ask(f"  {label}", default=str(cur) if cur else "", console=console)
                config.set(key, new_val)
                config.ensure_download_dir()
                print_success(f"Saved: {label} = {new_val}")
                time.sleep(0.7)
            except (KeyboardInterrupt, EOFError):
                pass
        else:
            print_warning(f"Enter a number from 1 to {reset_idx}")
            time.sleep(0.5)


# ─────────────────── PLAYLIST MENU ───────────────────

def handle_playlist(info: Dict[str, Any], url: str):
    """Playlist download menu with range selection."""
    entries = info.get("entries", [])
    total   = len(entries)

    console.print()
    console.print(_panel(
        f"  [{Colors.CYAN}]{Icons.PLAYLIST} Playlist: [bold]{escape(str(info.get('title') or '?')[:50])}[/bold][/]\n"
        f"  [{Colors.DIM}]{Icons.CHANNEL} {escape(str(info.get('uploader') or '?'))} • {total} videos[/]",
        f"{Icons.PLAYLIST} Playlist",
        Colors.MAGENTA,
    ))

    console.print()
    console.print(f"  [{Colors.YELLOW}]What to download?[/]")
    console.print(f"  [dim]1. First video only[/]")
    console.print(f"  [dim]2. Range (e.g. 1-5)[/]")
    console.print(f"  [dim]3. All videos ({total})[/]")
    console.print(f"  [dim]4. Cancel[/]")

    try:
        choice = Prompt.ask("\n  Choice", default="1")
    except (KeyboardInterrupt, EOFError):
        return

    if choice == "4":
        return
    elif choice == "1":
        selected = entries[:1]
    elif choice == "3":
        selected = entries
    elif choice == "2":
        try:
            rng = Prompt.ask("  Range (e.g. 1-5 or 3)", console=console)
            if "-" in rng:
                a, b = rng.split("-", 1)
                selected = entries[int(a)-1 : int(b)]
            else:
                idx = int(rng) - 1
                selected = entries[idx:idx+1]
        except Exception:
            print_warning("Invalid range — downloading first video.")
            selected = entries[:1]
    else:
        selected = entries[:1]

    console.print()
    print_info(f"Selected {len(selected)} video(s) to download.")

    for idx, entry in enumerate(selected, 1):
        entry_url = entry.get("url") or entry.get("webpage_url")
        if not entry_url:
            print_warning(f"Video #{idx}: no URL found, skipping.")
            continue

        console.print()
        console.print(Rule(
            f"[{Colors.CYAN}]{Icons.VIDEO} [{idx}/{len(selected)}] "
            f"{escape(str(entry.get('title') or entry_url)[:60])}[/]",
            style=Colors.BLUE,
        ))

        full_info = get_video_info(entry_url, config.to_ydl_cfg)
        if "error" in full_info:
            print_error(f"Error: {full_info['error']}")
            continue

        handle_single_download(entry_url, full_info)

        # Smart pause between videos
        if idx < len(selected):
            sleep_secs = inter_download_sleep(idx, len(selected))
            console.print()
            with Live(console=console, refresh_per_second=4) as live:
                deadline = time.time() + sleep_secs
                while time.time() < deadline:
                    left = deadline - time.time()
                    live.update(Align.left(
                        f"  [{Colors.DIM}]⏸  Cooldown before next video: {left:.1f}s[/]"
                    ))
                    time.sleep(0.25)

    console.print()
    print_success(f"Playlist done ({len(selected)} video(s)).")
    Prompt.ask("\n  Press Enter to continue")


# ─────────────────── SINGLE DOWNLOAD ───────────────────

def handle_single_download(url: str, info: Dict[str, Any]) -> bool:
    """Full download cycle: info → format → download → result. Returns True on success."""
    show_video_info(info)
    formats = get_available_formats(info)

    # Auto quality
    default_q = config.get("default_quality")
    if default_q != "ask":
        chosen_fmt = _auto_pick_format(formats, default_q)
        if chosen_fmt:
            console.print()
            print_info(f"Auto quality: {chosen_fmt['label']}")
        else:
            chosen_fmt = show_format_menu(formats)
    else:
        chosen_fmt = show_format_menu(formats)

    if not chosen_fmt:
        print_warning("Download cancelled.")
        return False

    # Confirmation
    if config.get("confirm_before_download"):
        console.print()
        if not Confirm.ask(f"  [{Colors.YELLOW}]Download {chosen_fmt['label']}?[/]"):
            print_warning("Cancelled.")
            return False

    # Download
    filepath = run_download(url, chosen_fmt, info)

    if not filepath or not os.path.exists(filepath):
        print_error("File not found after download.")
        return False

    show_success_panel(filepath, info, chosen_fmt)

    history.add(
        url=url,
        title=str(info.get("title") or "?"),
        uploader=str(info.get("uploader") or "?"),
        format_label=chosen_fmt["label"],
        filepath=filepath,
        filesize=os.path.getsize(filepath) if os.path.exists(filepath) else None,
        duration=info.get("duration"),
        success=True,
    )

    return True


def _auto_pick_format(formats, quality_key: str) -> Optional[Dict[str, Any]]:
    """Auto-select format by config key."""
    if quality_key == "best":
        return next((f for f in formats if f["type"] == "best"), None)
    elif quality_key == "audio":
        return next((f for f in formats if f["type"] == "audio"), None)
    elif quality_key.endswith("p"):
        try:
            h = int(quality_key[:-1])
            video_fmts = [f for f in formats if f.get("type") == "video"]
            return min(video_fmts, key=lambda f: abs(f.get("resolution", 0) - h), default=None)
        except Exception:
            return None
    return None


# ─────────────────── MAIN MENU ───────────────────

def show_main_menu() -> str:
    """Main menu. Returns user choice."""
    console.print()
    _print_divider()

    menu_items = [
        ("1", Icons.DOWNLOAD + " Download video / audio",   Colors.CYAN),
        ("2", Icons.PLAYLIST + " Download playlist",         Colors.MAGENTA),
        ("3", "📋 Download history",                         Colors.BLUE),
        ("4", Icons.SETTINGS + " Settings",                  Colors.YELLOW),
        ("5", f"{Icons.STUDIO} About",                       Colors.DIM),
        ("0", Icons.CANCEL   + " Exit",                      Colors.RED),
    ]

    table = Table(box=None, show_header=False, padding=(0, 2), expand=False)
    table.add_column("key",   width=3,  style=f"bold {Colors.YELLOW}")
    table.add_column("label", width=35)

    for key, label, color in menu_items:
        table.add_row(
            f"[{Colors.YELLOW}][{key}][/]",
            f"[{color}]{label}[/]",
        )

    console.print(Align.center(table))
    _print_divider()

    recent = history.get_recent(1)
    if recent:
        e = recent[0]
        console.print(
            Align.center(f"[{Colors.DIM}]Last: {escape(str(e.title or '?')[:40])}[/]")
        )

    console.print()
    try:
        choice = Prompt.ask(
            f"  [{Colors.YELLOW}]{Icons.ARROW} Choice[/]",
            choices=["0", "1", "2", "3", "4", "5"],
            console=console,
        )
    except (KeyboardInterrupt, EOFError):
        choice = "0"

    return choice


# ─────────────────── ABOUT ───────────────────

def show_about():
    """About screen with studio info."""
    console.clear()
    console.print()
    console.print(Align.center(LOGO))
    console.print(Align.center(LOGO_SUBTITLE))
    console.print(Align.center(LOGO_FOOTER))
    console.print()

    stats = session_stats()

    lines = [
        f"  [{Colors.CYAN}]RebornYoutubeSaver CLI v{APP_VERSION}[/]",
        f"  [{Colors.YELLOW}]By {STUDIO_NAME}[/]  [{Colors.DIM}]{STUDIO_GITHUB}[/]",
        f"  [{Colors.CYAN}]💬 Discord: {STUDIO_DISCORD}[/]",
        "",
        f"  [{Colors.DIM}]Powerful YouTube video & audio downloader[/]",
        f"  [{Colors.DIM}]Powered by yt-dlp + Rich[/]",
        "",
        f"  [{Colors.YELLOW}]Features:[/]",
        f"  {Icons.BULLET} Video up to 4K, audio MP3/M4A",
        f"  {Icons.BULLET} Playlists with range selection",
        f"  {Icons.BULLET} Rate-limit bypass (10 client strategies)",
        f"  {Icons.BULLET} Parallel fragment downloads",
        f"  {Icons.BULLET} Proxy & cookies support",
        f"  {Icons.BULLET} Download history",
        f"  {Icons.BULLET} Flexible settings",
        "",
        f"  [{Colors.YELLOW}]Session:[/]",
        f"  {Icons.BULLET} Requests: {stats['requests']}",
        f"  {Icons.BULLET} Rate-limit hits: {stats['ratelimit_hits']}",
        f"  {Icons.BULLET} Active client: {'+'.join(stats['current_client'])}",
        "",
        f"  [{Colors.DIM}]Download folder: {config.download_dir}[/]",
    ]

    console.print(_panel("\n".join(lines), f"{Icons.STUDIO} About", Colors.BLUE))
    Prompt.ask("\n  Press Enter to go back")


# ─────────────────── URL INPUT ───────────────────

def ask_url(mode: str = "video") -> Optional[str]:
    """Prompt user for a YouTube URL."""
    console.print()
    hint = "playlist" if mode == "playlist" else "video"

    while True:
        try:
            url = Prompt.ask(
                f"  [{Colors.CYAN}]{Icons.LINK} Paste YouTube {hint} URL (or Enter to cancel)[/]",
                default="",
                console=console,
            ).strip()
        except (KeyboardInterrupt, EOFError):
            return None

        if not url:
            return None

        if is_youtube_url(url):
            return url

        print_warning("That doesn't look like a YouTube URL. Try again (or press Enter to cancel).")


# ─────────────────── FETCH WITH ANIMATION ───────────────────

def fetch_info_animated(url: str) -> Dict[str, Any]:
    """Fetch video info with a spinner animation."""
    result = [None]

    def _fetch():
        result[0] = get_video_info(url, config.to_ydl_cfg)

    thread = threading.Thread(target=_fetch, daemon=True)
    thread.start()

    frames = SPINNER_DOTS
    i = 0
    with Live(console=console, refresh_per_second=15) as live:
        while thread.is_alive():
            spinner = frames[i % len(frames)]
            live.update(Align.center(
                f"[bold {Colors.CYAN}]{spinner}[/] [{Colors.DIM}]Fetching video info…[/]"
            ))
            i += 1
            time.sleep(0.07)
        live.update(Align.center(f"[{Colors.GREEN}]✓ Done![/]"))

    thread.join()
    return result[0] or {"error": "unknown", "details": "No result"}


def handle_info_error(info: Dict[str, Any]) -> bool:
    """Handle info fetch errors. Returns True if there was an error."""
    if "error" not in info:
        return False

    err  = info["error"]
    msgs = {
        "age_restricted": f"[{Colors.RED}]🔞 Age-restricted video. Cookies required.[/]",
        "unavailable":    f"[{Colors.RED}]❌ Video unavailable or removed.[/]",
        "private":        f"[{Colors.RED}]🔒 Private video.[/]",
        "members_only":   f"[{Colors.RED}]👑 Members-only content.[/]",
        "ratelimited":    f"[{Colors.WARNING}]⏳ YouTube rate-limited this request.\n"
                          f"  [{Colors.DIM}]Wait a few minutes and try again.[/]",
        "unknown":        f"[{Colors.RED}]❌ Error: {escape(str(info.get('details') or '?')[:200])}[/]",
    }
    console.print()
    console.print(Panel(
        msgs.get(err, msgs["unknown"]),
        border_style=Colors.RED,
        box=box.ROUNDED,
    ))
    return True


# ─────────────────── APP CLASS ───────────────────

class RebornApp:
    """Main CLI application entry point."""

    def run(self):
        show_splash()

        while True:
            console.clear()
            console.print()
            console.print(Align.center(LOGO))
            console.print(Align.center(LOGO_SUBTITLE))
            console.print(Align.center(LOGO_FOOTER))

            choice = show_main_menu()

            if choice == "0":
                self._exit()
                break
            elif choice == "1":
                self._download_single()
            elif choice == "2":
                self._download_playlist()
            elif choice == "3":
                show_history()
            elif choice == "4":
                show_settings()
            elif choice == "5":
                show_about()

    def _download_single(self):
        console.clear()
        console.print()
        console.print(Align.center(f"[bold {Colors.CYAN}]{Icons.DOWNLOAD} Download Video / Audio[/]"))
        console.print()

        url = ask_url("video")
        if not url:
            return

        info = fetch_info_animated(url)
        if handle_info_error(info):
            Prompt.ask("\n  Press Enter to go back")
            return

        if "entries" in info and info.get("_type") == "playlist":
            handle_playlist(info, url)
        else:
            handle_single_download(url, info)
            Prompt.ask("\n  Press Enter to continue")

    def _download_playlist(self):
        console.clear()
        console.print()
        console.print(Align.center(f"[bold {Colors.MAGENTA}]{Icons.PLAYLIST} Download Playlist[/]"))
        console.print()

        url = ask_url("playlist")
        if not url:
            return

        print_info("Fetching playlist info…")
        info = fetch_info_animated(url)
        if handle_info_error(info):
            Prompt.ask("\n  Press Enter to go back")
            return

        if "entries" not in info:
            print_warning("This is a single video, not a playlist. Downloading as one.")
            time.sleep(1)
            handle_single_download(url, info)
        else:
            handle_playlist(info, url)

        Prompt.ask("\n  Press Enter to continue")

    def _exit(self):
        console.print()
        console.print(Align.center(f"[{Colors.DIM}]Thanks for using RebornYoutubeSaver! — {STUDIO_NAME} 👋[/]"))
        console.print(Align.center(f"[{Colors.DIM}]💬 {STUDIO_DISCORD}   🐙 {STUDIO_GITHUB}[/]"))
        console.print()
        time.sleep(0.5)
