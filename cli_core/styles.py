"""
Styles, constants and ASCII art for RebornYoutubeSaver CLI.
Crafted by EleRiSey Studio.
"""

# ─────────────────── STUDIO ───────────────────
STUDIO_NAME    = "EleRiSey Studio"
STUDIO_GITHUB  = "github.com/yorikelesey-dot"
STUDIO_DISCORD = "discord.gg/RcKBmrn2rj"
APP_NAME       = "RebornYoutubeDowloader"
APP_VERSION    = "2.0.0"

# ─────────────────── ASCII LOGO ───────────────────
LOGO = r"""
[bold red]██████╗ [/bold red][bold yellow]███████╗[/bold yellow][bold green]██████╗ [/bold green][bold cyan] ██████╗ ██████╗ ███╗   ██╗[/bold cyan]
[bold red]██╔══██╗[/bold red][bold yellow]██╔════╝[/bold yellow][bold green]██╔══██╗[/bold green][bold cyan]██╔══██╗██╔══██╗████╗  ██║[/bold cyan]
[bold red]██████╔╝[/bold red][bold yellow]█████╗  [/bold yellow][bold green]██████╔╝[/bold green][bold cyan]██████╔╝██████╔╝██╔██╗ ██║[/bold cyan]
[bold red]██╔══██╗[/bold red][bold yellow]██╔══╝  [/bold yellow][bold green]██╔══██╗[/bold green][bold cyan]██╔══██╗██╔══██╗██║╚██╗██║[/bold cyan]
[bold red]██║  ██║[/bold red][bold yellow]███████╗[/bold yellow][bold green]██████╔╝[/bold green][bold cyan]██║  ██║██║  ██║██║ ╚████║[/bold cyan]
[bold red]╚═╝  ╚═╝[/bold red][bold yellow]╚══════╝[/bold yellow][bold green]╚═════╝ [/bold green][bold cyan]╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝[/bold cyan]"""

LOGO_SUBTITLE = (
    f"[dim]Youtube[/dim] [bold magenta]Saver[/bold magenta] "
    f"[dim]CLI v{APP_VERSION}[/dim]  [dim]by[/dim] "
    f"[bold yellow]{STUDIO_NAME}[/bold yellow]"
)

LOGO_FOOTER = (
    f"[dim]{STUDIO_GITHUB}[/dim]  "
    f"[cyan]discord.gg/RcKBmrn2rj[/cyan]"
)

# ─────────────────── SPINNER FRAMES ───────────────────
SPINNER_DOTS   = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
SPINNER_BAR    = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█", "▉", "▊", "▋", "▌", "▍", "▎"]
SPINNER_PULSE  = ["◐", "◓", "◑", "◒"]
SPINNER_WAVE   = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
SPINNER_CIRCLE = ["◜", "◠", "◝", "◞", "◡", "◟"]

# ─────────────────── PROGRESS CHARS ───────────────────
PROGRESS_FILL  = "█"
PROGRESS_HALF  = "▓"
PROGRESS_EMPTY = "░"
PROGRESS_TIP   = "▌"

# ─────────────────── COLOR PALETTE ───────────────────
class Colors:
    # Primary
    RED      = "#E63946"
    YELLOW   = "#FFD166"
    GREEN    = "#06D6A0"
    CYAN     = "#4CC9F0"
    BLUE     = "#4361EE"
    MAGENTA  = "#F72585"
    WHITE    = "#F8F9FA"
    DIM      = "#6C757D"
    WARNING  = "#F4A261"

    # Backgrounds
    BG_DARK   = "#0D1117"
    BG_CARD   = "#161B22"
    BG_BORDER = "#30363D"

    # Status
    SUCCESS = "#2FBF71"
    ERROR   = "#E63946"
    INFO    = "#4CC9F0"

    # Gradient (progress)
    GRAD_LOW  = "#E63946"
    GRAD_MID  = "#FFD166"
    GRAD_HIGH = "#06D6A0"

# ─────────────────── ICONS ───────────────────
class Icons:
    VIDEO    = "🎬"
    AUDIO    = "🎵"
    DOWNLOAD = "📥"
    UPLOAD   = "📤"
    SPEED    = "⚡"
    ETA      = "⏱️"
    SIZE     = "📦"
    QUALITY  = "✨"
    PLAYLIST = "📋"
    CHANNEL  = "👤"
    VIEWS    = "👁️"
    LIKES    = "❤️"
    STAR     = "⭐"
    CHECK    = "✅"
    CROSS    = "❌"
    WARNING  = "⚠️"
    INFO     = "ℹ️"
    SETTINGS = "⚙️"
    FOLDER   = "📁"
    LINK     = "🔗"
    SEARCH   = "🔍"
    ROCKET   = "🚀"
    FIRE     = "🔥"
    SPARKLE  = "✨"
    DONE     = "🎉"
    CANCEL   = "🚫"
    BACK     = "◀"
    NEXT     = "▶"
    ARROW    = "→"
    BULLET   = "•"
    STUDIO   = "🏢"

# ─────────────────── FORMAT LABELS ───────────────────
RESOLUTION_EMOJI = {
    "2160p": "🎬 4K",
    "1440p": "📹 2K",
    "1080p": "🎥 FHD",
    "720p":  "📺 HD",
    "480p":  "📱 SD",
    "360p":  "📲 360p",
    "240p":  "🔅 240p",
}
