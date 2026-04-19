"""
Downloader — yt-dlp wrapper with integrated rate-limit bypass.
All YouTube requests run through bypass.with_retry().

By EleRiSey Studio — github.com/yorikelesey-dot
discord.gg/RcKBmrn2rj
"""


import os
import time
from typing import Optional, List, Dict, Any, Callable
import yt_dlp

from .styles import Icons, RESOLUTION_EMOJI
from .bypass import (
    build_bypass_opts, with_retry, session,
    inter_download_sleep, classify_error,
)


# ─────────────────── PROGRESS ───────────────────

class DownloadInfo:
    """Структура прогресса скачивания (используем __slots__ для скорости)."""
    __slots__ = (
        "status", "percent", "speed", "eta",
        "downloaded", "total", "filename",
        "fragment_idx", "fragment_count", "elapsed",
        "client_used", "attempt",
    )

    def __init__(self):
        self.status         = "waiting"
        self.percent        = 0.0
        self.speed          = 0.0
        self.eta: Optional[int] = None
        self.downloaded     = 0
        self.total: Optional[int] = None
        self.filename       = ""
        self.fragment_idx   = 0
        self.fragment_count = 0
        self.elapsed        = 0.0
        self.client_used    = ""
        self.attempt        = 1


# ─────────────────── INFO EXTRACTION ───────────────────

def get_video_info(url: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Извлекает метаданные с автоматическим retry + rotate client.
    """
    def _do_extract(opts, _url):
        opts = dict(opts)
        opts["extract_flat"] = "discard_in_playlist"
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(_url, download=False)
            return ydl.sanitize_info(info)

    try:
        return with_retry(_do_extract, url, cfg, max_attempts=4)
    except yt_dlp.utils.DownloadError as e:
        msg = str(e)
        # Последняя попытка — без cookies (могут мешать)
        if "cookie" in msg.lower():
            try:
                cfg2 = {k: v for k, v in cfg.items() if k not in ("cookies_path", "cookies_browser")}
                return with_retry(_do_extract, url, cfg2, max_attempts=2)
            except Exception as e2:
                msg = str(e2)
        return _classify_dl_error(msg)
    except Exception as e:
        return {"error": "unknown", "details": str(e)[:300]}


def _classify_dl_error(msg: str) -> Dict[str, Any]:
    """Переводит строку ошибки в стандартный error-словарь."""
    m = msg.lower()
    if "sign in to confirm" in m or "age" in m:
        return {"error": "age_restricted"}
    if "video unavailable" in m:
        return {"error": "unavailable"}
    if "private video" in m:
        return {"error": "private"}
    if "members-only" in m:
        return {"error": "members_only"}
    if "429" in m or "too many" in m or "rate" in m:
        return {"error": "ratelimited", "details": "YouTube временно ограничил запросы. Подожди несколько минут."}
    return {"error": "unknown", "details": msg[:300]}


# ─────────────────── FORMATS ───────────────────

def get_available_formats(info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Разбирает форматы на группы: best / video / audio."""
    result = []
    raw_formats = info.get("formats", [])

    # ── Best (auto) ──
    result.append({
        "id":       "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "label":    f"{Icons.STAR} Лучшее (авто)",
        "ext":      "mp4",
        "type":     "best",
        "filesize": None,
        "note":     "Наилучшее доступное качество",
    })

    # ── Video resolutions ──
    heights_seen = set()
    for f in sorted(raw_formats, key=lambda x: x.get("height") or 0, reverse=True):
        h = f.get("height")
        vcodec = f.get("vcodec", "none")
        if not h or vcodec == "none" or h < 240:
            continue
        if h in heights_seen:
            continue
        heights_seen.add(h)

        res_str    = f"{h}p"
        label_base = RESOLUTION_EMOJI.get(res_str, f"🎞️ {res_str}")

        size = None
        for ff in raw_formats:
            if ff.get("height") == h:
                size = ff.get("filesize") or ff.get("filesize_approx")
                if size:
                    break

        fps       = f.get("fps") or ""
        fps_note  = f" {fps}fps" if fps and fps > 30 else ""
        vcodec_str = str(f.get("vcodec", ""))
        codec_note = " [AV1]" if "av01" in vcodec_str else (" [VP9]" if "vp9" in vcodec_str else "")

        result.append({
            "id":         (
                f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]"
                f"/bestvideo[height<={h}]+bestaudio"
                f"/best[height<={h}]/best"
            ),
            "label":      f"{label_base}{fps_note}{codec_note}",
            "ext":        "mp4",
            "type":       "video",
            "filesize":   size,
            "resolution": h,
            "note":       f"{h}p видео + лучшее аудио",
        })

    # ── Audio only ──
    audio_fmts = [f for f in raw_formats
                  if f.get("vcodec") == "none" and f.get("acodec") != "none"]
    if audio_fmts:
        best_a = max(audio_fmts, key=lambda f: f.get("abr") or 0)
        abr    = best_a.get("abr") or "?"
        aext   = best_a.get("ext", "m4a")
        asize  = best_a.get("filesize") or best_a.get("filesize_approx")

        result.append({
            "id":       "bestaudio[ext=m4a]/bestaudio",
            "label":    f"{Icons.AUDIO} Только аудио ({abr}kbps, {aext.upper()})",
            "ext":      aext,
            "type":     "audio",
            "filesize": asize,
            "note":     "Только звук, без видео",
        })
        result.append({
            "id":              "bestaudio/best",
            "label":           f"{Icons.AUDIO} MP3 (конвертация)",
            "ext":             "mp3",
            "type":            "audio_mp3",
            "filesize":        asize,
            "note":            "Конвертируется в MP3 через ffmpeg",
            "postprocessors":  [{"key": "FFmpegExtractAudio",
                                 "preferredcodec": "mp3", "preferredquality": "320"}],
        })

    return result


# ─────────────────── DOWNLOAD ───────────────────

def download_video(
    url: str,
    fmt: Dict[str, Any],
    output_dir: str,
    cfg: Dict[str, Any],
    on_progress: Optional[Callable[["DownloadInfo"], None]] = None,
    output_template: Optional[str] = None,
) -> Optional[str]:
    """
    Скачивает видео/аудио с умным обходом рейт-лимитов.

    Returns:
        Путь к файлу или None при ошибке.
    """
    dl_info      = DownloadInfo()
    result_path: list = [None]
    start_time   = time.time()
    attempt_no   = [1]

    tmpl = output_template or os.path.join(
        output_dir, "%(uploader)s — %(title)s [%(id)s].%(ext)s"
    )

    # ── Progress hooks ──

    def _progress_hook(d):
        status = d.get("status", "")
        dl_info.elapsed = time.time() - start_time

        if status == "downloading":
            dl_info.status = "downloading"
            total      = d.get("total_bytes") or d.get("total_bytes_estimate")
            downloaded = d.get("downloaded_bytes", 0)
            dl_info.downloaded = downloaded
            dl_info.total      = total

            if total and total > 0:
                dl_info.percent = min(100.0, downloaded / total * 100)
            else:
                try:
                    raw = d.get("_percent_str", "0%").replace("%", "").strip()
                    dl_info.percent = float(raw)
                except Exception:
                    pass

            dl_info.speed = d.get("speed") or 0.0
            dl_info.eta   = d.get("eta")
            dl_info.filename = d.get("filename", "")

            fi = d.get("fragment_index")
            fc = d.get("fragment_count")
            if fi is not None:
                dl_info.fragment_idx   = fi
                dl_info.fragment_count = fc or 0

        elif status == "finished":
            dl_info.status  = "merging"
            dl_info.percent = 100.0
            fp = d.get("filename") or d.get("info_dict", {}).get("filepath")
            if fp:
                result_path[0] = fp

        elif status == "error":
            dl_info.status = "error"

        if on_progress:
            on_progress(dl_info)

    def _postprocessor_hook(d):
        if d.get("status") == "started":
            dl_info.status = "processing"
            if on_progress:
                on_progress(dl_info)
        elif d.get("status") == "finished":
            dl_info.status = "done"
            fp = d.get("info_dict", {}).get("filepath") or d.get("filepath")
            if fp:
                result_path[0] = fp
            if on_progress:
                on_progress(dl_info)

    # ── Core download fn (передаётся в with_retry) ──

    def _do_download(opts, _url):
        opts = dict(opts)
        opts.update({
            "format":             fmt["id"],
            "outtmpl":            tmpl,
            "merge_output_format": "mp4" if fmt["type"] not in ("audio_mp3",) else None,
            "noprogress":         True,
            "progress_hooks":     [_progress_hook],
            "postprocessor_hooks": [_postprocessor_hook],
        })

        # Субтитры
        if cfg.get("subtitles"):
            opts.update({
                "writesubtitles": True,
                "subtitleslangs": ["ru", "en"],
                "embedsubtitles": True,
            })

        # Обложка
        if cfg.get("embed_thumbnail"):
            opts["embedthumbnail"] = True

        # MP3 постпроцессор
        if fmt.get("postprocessors"):
            opts["postprocessors"] = fmt["postprocessors"]

        # Лимит размера
        if cfg.get("max_filesize"):
            opts["max_filesize"] = cfg["max_filesize"]

        # Отмечаем клиент в dl_info
        clients = opts.get("extractor_args", {}).get("youtube", {}).get("player_client", [])
        dl_info.client_used = "+".join(clients) if clients else "?"
        dl_info.attempt     = attempt_no[0]

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(_url, download=True)

            # Получаем путь к файлу
            if not result_path[0]:
                requested = info.get("requested_downloads", [{}])
                if requested:
                    result_path[0] = (
                        requested[0].get("filepath") or
                        requested[0].get("filename")
                    )
            if not result_path[0]:
                result_path[0] = info.get("_filename")

        return result_path[0]

    def _on_retry_status(status: str, attempt: int, backoff: float):
        """Прокидываем статус retry в прогресс."""
        attempt_no[0] = attempt
        dl_info.attempt = attempt
        if "ratelimit" in status:
            dl_info.status = "ratelimited"
        elif "transient" in status:
            dl_info.status = "retry"
        else:
            dl_info.status = "retry"
        if on_progress:
            on_progress(dl_info)

    # ── Запускаем через bypass.with_retry ──
    try:
        with_retry(
            _do_download, url, cfg,
            max_attempts=int(cfg.get("retries", 6)),
            on_status=_on_retry_status,
        )
    except yt_dlp.utils.DownloadError as e:
        msg   = str(e)
        etype = classify_error(msg)

        # Форматный fallback
        if "Requested format is not available" in msg or etype == "unknown":
            for fb in [
                "bestvideo+bestaudio/best",
                "best[ext=mp4]/best",
                "best",
            ]:
                if fb == fmt["id"]:
                    continue
                try:
                    fmt_copy = dict(fmt, id=fb)
                    with_retry(
                        lambda opts, u: _do_download(dict(opts, **{"format": fb}), u),
                        url, cfg, max_attempts=2,
                    )
                    break
                except Exception:
                    continue

        if not result_path[0]:
            dl_info.status = "error"
            if on_progress:
                on_progress(dl_info)
            return None

    except Exception:
        dl_info.status = "error"
        if on_progress:
            on_progress(dl_info)
        return None

    # ── Верификация файла ──
    path = result_path[0]
    if path and os.path.exists(path):
        session.on_success()
        dl_info.status = "done"
        if on_progress:
            on_progress(dl_info)
        return path

    # Поиск по расширениям если путь «почти» верный
    if path:
        base = os.path.splitext(path)[0]
        for ext in ("mp4", "mkv", "webm", "m4a", "mp3", "opus", "ogg"):
            candidate = f"{base}.{ext}"
            if os.path.exists(candidate):
                session.on_success()
                return candidate

    return None


# ─────────────────── PLAYLIST ───────────────────

def get_playlist_info(url: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Извлекает плоский список плейлиста без скачивания."""
    def _do(opts, _url):
        opts = dict(opts, extract_flat=True, skip_download=True)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(_url, download=False)
            return ydl.sanitize_info(info)

    try:
        return with_retry(_do, url, cfg, max_attempts=3)
    except Exception as e:
        return {"error": "unknown", "details": str(e)[:200]}
