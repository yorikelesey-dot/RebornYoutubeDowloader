"""
Download history manager — JSON-backed persistent log.
By EleRiSey Studio — github.com/yorikelesey-dot
discord.gg/RcKBmrn2rj
"""


import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

_HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "download_history.json"
)


class HistoryEntry:
    def __init__(self, data: Dict[str, Any]):
        self.url:       str            = data.get("url", "")
        self.title:     str            = data.get("title", "")
        self.uploader:  str            = data.get("uploader", "")
        self.format:    str            = data.get("format", "")
        self.filepath:  str            = data.get("filepath", "")
        self.filesize:  Optional[int]  = data.get("filesize")
        self.duration:  Optional[int]  = data.get("duration")
        self.timestamp: str            = data.get("timestamp", datetime.now().isoformat())
        self.success:   bool           = data.get("success", True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url":       self.url,
            "title":     self.title,
            "uploader":  self.uploader,
            "format":    self.format,
            "filepath":  self.filepath,
            "filesize":  self.filesize,
            "duration":  self.duration,
            "timestamp": self.timestamp,
            "success":   self.success,
        }


class DownloadHistory:
    def __init__(self, limit: int = 100):
        self._limit = limit
        self._entries: List[HistoryEntry] = []
        self._load()

    def _load(self):
        if os.path.exists(_HISTORY_FILE):
            try:
                with open(_HISTORY_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self._entries = [HistoryEntry(e) for e in raw[-self._limit:]]
            except Exception:
                self._entries = []

    def _save(self):
        try:
            with open(_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump([e.to_dict() for e in self._entries], f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def add(
        self,
        url: str,
        title: str,
        uploader: str,
        format_label: str,
        filepath: str,
        filesize: Optional[int] = None,
        duration: Optional[int] = None,
        success: bool = True,
    ):
        entry = HistoryEntry({
            "url":       url,
            "title":     title,
            "uploader":  uploader,
            "format":    format_label,
            "filepath":  filepath,
            "filesize":  filesize,
            "duration":  duration,
            "timestamp": datetime.now().isoformat(),
            "success":   success,
        })
        self._entries.append(entry)
        if len(self._entries) > self._limit:
            self._entries = self._entries[-self._limit:]
        self._save()

    def get_recent(self, n: int = 20) -> List[HistoryEntry]:
        return list(reversed(self._entries[-n:]))

    def clear(self):
        self._entries = []
        self._save()

    def __len__(self):
        return len(self._entries)


# Singleton
history = DownloadHistory()
