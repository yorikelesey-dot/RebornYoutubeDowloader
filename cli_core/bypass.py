"""
YouTube Rate-Limit Bypass — smart, free strategies to avoid throttling.

Strategies (100% free, no proxy required):
  1. Player client rotation   — each attempt uses a different YT client
  2. Exponential backoff      — growing sleep on 429 / throttle
  3. Session-level request counter
  4. Realistic HTTP headers   — matching each client's expected UA
  5. Fragment concurrency     — automatically reduced under throttle
  6. Human-like request spacing
  7. Smart error classifier   — 429 / 403 / signIn / transient

By EleRiSey Studio — github.com/yorikelesey-dot
discord.gg/RcKBmrn2rj
"""

import time
import random
import threading
from typing import Optional, Dict, Any, List, Callable

# ─────────────────── PLAYER CLIENTS ───────────────────
# Ordered from most reliable to least.
PLAYER_CLIENTS: List[List[str]] = [
    ["android"],
    ["ios"],
    ["android", "web"],
    ["tv_embedded"],
    ["web_embedded"],
    ["mweb"],
    ["ios", "tv_embedded"],
    ["android_embedded"],
    ["web"],
    ["android", "ios", "web"],
]

# HTTP headers matching each client
_CLIENT_HEADERS: Dict[str, Dict[str, str]] = {
    "android": {
        "User-Agent": (
            "com.google.android.youtube/19.29.37 "
            "(Linux; U; Android 11; Pixel 5 Build/RQ3A.210805.001) gzip"
        ),
        "X-YouTube-Client-Name":    "3",
        "X-YouTube-Client-Version": "19.29.37",
    },
    "ios": {
        "User-Agent": (
            "com.google.ios.youtube/19.29.1 "
            "(iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X)"
        ),
        "X-YouTube-Client-Name":    "5",
        "X-YouTube-Client-Version": "19.29.1",
    },
    "web": {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "X-YouTube-Client-Name":    "1",
        "X-YouTube-Client-Version": "2.20240520.00.00",
    },
    "mweb": {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 10; Pixel 4) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Mobile Safari/537.36"
        ),
    },
    "tv_embedded": {
        "User-Agent": (
            "Mozilla/5.0 (SMART-TV; Linux; Tizen 6.5) "
            "AppleWebKit/538.1 (KHTML, like Gecko) Version/6.5 TV Safari/538.1"
        ),
    },
}

# ─────────────────── ERROR CLASSIFICATION ───────────────────

_RATELIMIT_PHRASES = (
    "HTTP Error 429", "Too Many Requests", "HTTP Error 403: Forbidden",
    "Sign in to confirm", "Please wait", "rate limit", "throttl",
    "Precondition Failed", "This content isn't available",
    "nsig extraction failed",
)

_TRANSIENT_PHRASES = (
    "Connection reset", "RemoteDisconnected", "Read timed out",
    "Network is unreachable", "Temporary failure in name resolution",
    "IncompleteRead",
)

_FATAL_PHRASES = (
    "Video unavailable", "Private video", "This video has been removed",
    "members-only", "age-restricted", "This video requires payment",
)


def classify_error(msg: str) -> str:
    """
    Classify a yt-dlp error string.

    Returns:
        'ratelimit'  — backoff + client rotate needed
        'transient'  — network glitch, quick retry
        'fatal'      — content unavailable, no point retrying
        'unknown'    — attempt one more retry
    """
    ml = msg.lower()
    for p in _FATAL_PHRASES:
        if p.lower() in ml:
            return "fatal"
    for p in _RATELIMIT_PHRASES:
        if p.lower() in ml:
            return "ratelimit"
    for p in _TRANSIENT_PHRASES:
        if p.lower() in ml:
            return "transient"
    return "unknown"


# ─────────────────── SESSION STATE ───────────────────

class _SessionState:
    """Global per-process request counter and backoff tracker."""

    def __init__(self):
        self._lock           = threading.Lock()
        self._request_count  = 0
        self._ratelimit_hits = 0
        self._last_request   = 0.0
        self._backoff_until  = 0.0
        self._client_index   = 0

    def pre_request(self, min_gap: float = 0.5):
        """Call before every yt-dlp request. Enforces pacing."""
        with self._lock:
            now = time.time()
            if now < self._backoff_until:
                time.sleep(self._backoff_until - now)
            gap = time.time() - self._last_request
            if gap < min_gap:
                time.sleep(min_gap - gap + random.uniform(0.1, 0.4))
            self._last_request = time.time()
            self._request_count += 1

    def on_ratelimit(self) -> float:
        """Call on a 429 / throttle. Returns how long to wait."""
        with self._lock:
            self._ratelimit_hits += 1
            # Exponential backoff: 10s → 30s → 90s → 270s (cap 300s)
            delay  = min(10 * (3 ** (self._ratelimit_hits - 1)), 300)
            jitter = random.uniform(0, delay * 0.2)
            self._backoff_until = time.time() + delay + jitter
            self._client_index  = (self._client_index + 1) % len(PLAYER_CLIENTS)
        return delay

    def on_success(self):
        """Call after a successful download."""
        with self._lock:
            if self._ratelimit_hits > 0:
                self._ratelimit_hits = max(0, self._ratelimit_hits - 1)

    def next_client(self) -> List[str]:
        with self._lock:
            return PLAYER_CLIENTS[self._client_index % len(PLAYER_CLIENTS)]

    def rotate_client(self) -> List[str]:
        with self._lock:
            self._client_index = (self._client_index + 1) % len(PLAYER_CLIENTS)
            return PLAYER_CLIENTS[self._client_index]

    @property
    def backoff_remaining(self) -> float:
        return max(0.0, self._backoff_until - time.time())

    @property
    def request_count(self) -> int:
        return self._request_count

    @property
    def ratelimit_hits(self) -> int:
        return self._ratelimit_hits


# Singleton — one per process
session = _SessionState()


# ─────────────────── OPTIONS BUILDER ───────────────────

def build_bypass_opts(
    cfg: Dict[str, Any],
    client_override: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build optimal yt-dlp options with rate-limit bypass baked in.

    - Picks the current player_client from the rotation
    - Adds realistic HTTP headers
    - Sets human-like sleep intervals
    - Enables geo_bypass
    - Configures retries and fragment_retries
    """
    opts: Dict[str, Any] = {
        "quiet":       True,
        "no_warnings": True,
        "noprogress":  True,
        "geo_bypass":  True,

        # Retry configuration
        "retries":              int(cfg.get("retries", 6)),
        "fragment_retries":     10,
        "file_access_retries":  5,
        "retry_sleep_functions": {"http": lambda n: min(4 * 2 ** n, 120)},

        # Human-like pacing
        "sleep_interval":          random.uniform(0.8, 2.0),
        "max_sleep_interval":      5.0,
        "sleep_interval_requests": random.uniform(0.3, 1.0),
        "sleep_interval_subtitles": 1,

        # Reduce concurrency under throttle
        "concurrent_fragment_downloads": _safe_concurrent(cfg),

        "socket_timeout": 30,
    }

    if cfg.get("proxy"):
        opts["proxy"] = cfg["proxy"]

    if cfg.get("rate_limit"):
        opts["ratelimit"] = cfg["rate_limit"]

    # Cookies
    cookie_path    = cfg.get("cookies_path", "cookies.txt")
    cookie_browser = cfg.get("cookies_browser", "")
    if cookie_path and __import__("os").path.exists(cookie_path):
        opts["cookiefile"] = cookie_path
    elif cookie_browser:
        opts["cookiesfrombrowser"] = (cookie_browser,)

    # Player client rotation
    clients  = client_override or session.next_client()
    po_token = cfg.get("po_token", "")

    opts["extractor_args"] = {
        "youtube": {
            "player_client": clients,
            **({"po_token": [po_token]} if po_token else {}),
            "skip": ["hls", "dash"] if session.ratelimit_hits >= 2 else [],
        }
    }

    # HTTP headers matching the primary client
    primary = clients[0] if clients else "android"
    opts["http_headers"] = dict(_CLIENT_HEADERS.get(primary, _CLIENT_HEADERS["android"]))

    return opts


def _safe_concurrent(cfg: Dict[str, Any]) -> int:
    """Reduce concurrent fragments when YouTube is throttling."""
    base = int(cfg.get("concurrent_fragments", 4))
    hits = session.ratelimit_hits
    if hits == 0: return base
    if hits == 1: return max(2, base // 2)
    if hits == 2: return 2
    return 1


# ─────────────────── RETRY WRAPPER ───────────────────

def with_retry(
    fn: Callable,
    url: str,
    cfg: Dict[str, Any],
    max_attempts: int = 5,
    on_status: Optional[Callable[[str, int, float], None]] = None,
) -> Any:
    """
    Universal retry wrapper for any yt-dlp call.

    Args:
        fn:           callable(opts, url) -> result
        url:          YouTube URL (for logging)
        cfg:          session config dict
        max_attempts: maximum retry count
        on_status:    callback(status, attempt, backoff_secs)
    """
    import yt_dlp
    last_exc = Exception("No attempts made")

    for attempt in range(1, max_attempts + 1):
        session.pre_request(min_gap=0.5 + session.ratelimit_hits * 0.5)

        clients = session.next_client() if attempt == 1 else PLAYER_CLIENTS[(attempt - 1) % len(PLAYER_CLIENTS)]
        opts    = build_bypass_opts(cfg, client_override=clients)

        try:
            result = fn(opts, url)
            session.on_success()
            return result

        except yt_dlp.utils.DownloadError as e:
            msg    = str(e)
            etype  = classify_error(msg)
            last_exc = e

            if etype == "fatal":
                raise

            if etype == "ratelimit":
                delay = session.on_ratelimit()
                if on_status:
                    on_status(f"rate_limit:attempt_{attempt}", attempt, delay)
                if attempt < max_attempts:
                    time.sleep(delay)
                continue

            if etype == "transient":
                delay = min(3 * attempt, 30)
                if on_status:
                    on_status(f"transient:attempt_{attempt}", attempt, delay)
                if attempt < max_attempts:
                    time.sleep(delay + random.uniform(0.5, 2.0))
                continue

            session.rotate_client()
            if attempt < max_attempts:
                time.sleep(2 + random.uniform(0, 3))
            continue

        except Exception as e:
            last_exc = e
            if attempt < max_attempts:
                time.sleep(2 + attempt)
            continue

    raise last_exc


# ─────────────────── SMART SLEEP ───────────────────

def inter_download_sleep(video_index: int, total: int) -> float:
    """
    Compute cooldown between playlist videos.
    Grows with each rate-limit hit to stay safe.
    """
    hits = session.ratelimit_hits
    if hits == 0 and video_index < 5:
        return random.uniform(1.0, 3.0)
    elif hits == 0:
        return random.uniform(2.0, 5.0)
    elif hits == 1:
        return random.uniform(8.0, 15.0)
    elif hits == 2:
        return random.uniform(20.0, 40.0)
    return random.uniform(45.0, 90.0)


# ─────────────────── SESSION STATS ───────────────────

def session_stats() -> Dict[str, Any]:
    """Return current session statistics."""
    return {
        "requests":       session.request_count,
        "ratelimit_hits": session.ratelimit_hits,
        "current_client": session.next_client(),
        "backoff_left":   round(session.backoff_remaining, 1),
    }
