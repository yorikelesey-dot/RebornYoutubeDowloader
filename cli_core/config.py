"""
Configuration manager — JSON-backed settings with defaults.
By EleRiSey Studio — github.com/yorikelesey-dot
discord.gg/RcKBmrn2rj
"""

import os
import json
from typing import Any, Dict, Optional

_CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "cli_config.json"
)

_DEFAULTS: Dict[str, Any] = {
    # Download
    "download_dir":        "downloads",
    "output_template":     "%(uploader)s — %(title)s [%(id)s].%(ext)s",
    "concurrent_fragments": 4,
    "rate_limit":          0,      # 0 = unlimited (bytes/s)
    "max_filesize":        0,      # 0 = unlimited
    "retries":             6,

    # Quality default
    "default_quality": "ask",     # ask | best | 1080p | 720p | 480p | audio

    # Extra features
    "subtitles":        False,
    "embed_thumbnail":  False,
    "geo_bypass":       True,
    "sponsorblock":     False,
    "sponsorblock_categories": ["sponsor", "intro", "outro"],

    # Network
    "proxy":           "",
    "cookies_path":    "cookies.txt",
    "cookies_browser": "",
    "po_token":        "",

    # UI
    "auto_open_folder":          False,
    "confirm_before_download":   True,
    "history_limit":             100,
}


class Config:
    """RebornYoutubeSaver CLI configuration."""

    def __init__(self):
        self._data: Dict[str, Any] = dict(_DEFAULTS)
        self._load()

    def _load(self):
        if os.path.exists(_CONFIG_FILE):
            try:
                with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._data = {**_DEFAULTS, **saved}
            except Exception:
                pass

    def save(self):
        try:
            with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default if default is not None else _DEFAULTS.get(key))

    def set(self, key: str, value: Any):
        self._data[key] = value
        self.save()

    def reset(self, key: Optional[str] = None):
        """Reset one key or all to defaults."""
        if key:
            self._data[key] = _DEFAULTS.get(key)
        else:
            self._data = dict(_DEFAULTS)
        self.save()

    def as_dict(self) -> Dict[str, Any]:
        return dict(self._data)

    def ensure_download_dir(self) -> str:
        """Create download folder if it doesn't exist. Returns path."""
        d = self.get("download_dir")
        os.makedirs(d, exist_ok=True)
        return d

    # ── Shorthand properties ──

    @property
    def download_dir(self) -> str:
        return self.get("download_dir")

    @property
    def output_template(self) -> str:
        return os.path.join(self.download_dir, self.get("output_template"))

    @property
    def concurrent_fragments(self) -> int:
        return int(self.get("concurrent_fragments", 4))

    @property
    def rate_limit(self) -> Optional[int]:
        v = int(self.get("rate_limit", 0))
        return v if v > 0 else None

    @property
    def max_filesize(self) -> Optional[int]:
        v = int(self.get("max_filesize", 0))
        return v if v > 0 else None

    @property
    def to_ydl_cfg(self) -> Dict[str, Any]:
        """Convert config to dict for the downloader."""
        return {
            "proxy":                self.get("proxy") or None,
            "rate_limit":           self.rate_limit,
            "cookies_path":         self.get("cookies_path"),
            "cookies_browser":      self.get("cookies_browser"),
            "po_token":             self.get("po_token"),
            "concurrent_fragments": self.concurrent_fragments,
            "subtitles":            self.get("subtitles"),
            "embed_thumbnail":      self.get("embed_thumbnail"),
            "geo_bypass":           self.get("geo_bypass"),
            "max_filesize":         self.max_filesize,
            "retries":              int(self.get("retries", 6)),
        }


# Singleton
config = Config()
