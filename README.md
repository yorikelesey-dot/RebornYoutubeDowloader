<div align="center">

```
██████╗ ███████╗██████╗  ██████╗ ██████╗ ███╗   ██╗
██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔══██╗████╗  ██║
██████╔╝█████╗  ██████╔╝██████╔╝██████╔╝██╔██╗ ██║
██╔══██╗██╔══╝  ██╔══██╗██╔══██╗██╔══██╗██║╚██╗██║
██║  ██║███████╗██████╔╝██║  ██║██║  ██║██║ ╚████║
╚═╝  ╚═╝╚══════╝╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
```

**RebornYoutubeDowloader CLI v2.0**

*A powerful, beautiful terminal YouTube downloader*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)](https://www.python.org)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red?style=flat-square)](https://github.com/yt-dlp/yt-dlp)
[![Rich](https://img.shields.io/badge/Rich-UI-blueviolet?style=flat-square)](https://github.com/Textualize/rich)
[![Made by EleRiSey](https://img.shields.io/badge/Made%20by-EleRiSey%20Studio-orange?style=flat-square)](https://github.com/yorikelesey-dot)
[![Discord](https://img.shields.io/badge/Discord-Join-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.gg/RcKBmrn2rj)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎬 **4K Video** | Choose from 2160p, 1440p, 1080p, 720p, 480p, 360p |
| 🎵 **Audio** | M4A (lossless) or MP3 320kbps via ffmpeg |
| 📋 **Playlists** | Download all, first, or a range (e.g. `1-5`) |
| 🛡️ **Rate-limit bypass** | 10 client strategies, exponential backoff, header rotation |
| ⚡ **Parallel fragments** | Up to 16 concurrent streams, auto-reduced on throttle |
| 📊 **Live progress** | Speed, ETA, fragment count, client switching — all visible |
| 📋 **History** | Last 100 downloads with date, format, size |
| ⚙️ **Settings** | Persistent JSON config, no `.env` required |
| 🌐 **Proxy** | http / https / socks5 |
| 🍪 **Cookies** | From file or browser (Chrome, Firefox, Edge…) |
| 🌍 **Geo-bypass** | Automatic geographic restriction bypass |

---

## 🚀 Quick Start

### Requirements

```bash
# Python 3.10+
pip install yt-dlp rich
```

> **FFmpeg** is required for merging video+audio streams and MP3 conversion.  
> Download: https://ffmpeg.org/download.html — add to PATH.

### Run

```bash
git clone https://github.com/yorikelesey-dot/RebornYoutubeDowloader
cd RebornYoutubeDowloader
pip install yt-dlp rich
python cli.py
```

> ⚠️ **Windows users:** run from **PowerShell** (not CMD) for correct color and Unicode rendering.

---

## 🎮 Usage

```
[1] Download video / audio    — paste a YouTube URL and choose quality
[2] Download playlist         — choose all, first, or a range
[3] Download history          — view and clear past downloads
[4] Settings                  — configure all options
[5] About                     — version, session stats, studio info
[0] Exit
```

### Supported URL formats

```
https://youtube.com/watch?v=...
https://youtu.be/...
https://youtube.com/shorts/...
https://youtube.com/playlist?list=...
```

---

## 🛡️ Rate-Limit Bypass

RebornYoutubeSaver includes a built-in bypass engine — **no proxy needed**:

| Strategy | How it works |
|---|---|
| **10 player clients** | Rotates: `android`, `ios`, `tv_embedded`, `mweb`, `web_embedded`… |
| **Realistic headers** | Per-client `User-Agent` and `X-YouTube-Client-*` headers |
| **Exponential backoff** | 429 → 10s → 30s → 90s → 270s with jitter |
| **Error classification** | Detects `ratelimit` / `transient` / `fatal` — different retry logic |
| **Auto concurrency** | `concurrent_fragments` drops to 1 under heavy throttle |
| **Inter-video sleep** | Smart cooldown between playlist videos grows with hit count |
| **Fragment retries** | 10 retries per fragment, 6 retries per file |

---

## ⚙️ Settings

Access via the **Settings** menu (`[4]`) in the app:

| Setting | Default | Description |
|---|---|---|
| `download_dir` | `downloads` | Output folder |
| `concurrent_fragments` | `4` | Parallel download streams |
| `rate_limit` | `0` | Speed cap in bytes/s (0 = unlimited) |
| `default_quality` | `ask` | `ask` / `best` / `1080p` / `720p` / `audio` |
| `subtitles` | `false` | Download & embed subtitles (ru, en) |
| `embed_thumbnail` | `false` | Embed cover art into file |
| `geo_bypass` | `true` | Bypass geographic restrictions |
| `sponsorblock` | `false` | Skip sponsor segments |
| `proxy` | — | e.g. `http://127.0.0.1:8080` |
| `cookies_path` | `cookies.txt` | Path to Netscape cookies file |
| `cookies_browser` | — | `chrome` / `firefox` / `edge` |
| `confirm_before_download` | `true` | Ask before starting |
| `auto_open_folder` | `false` | Open folder on completion |

All settings are saved to `cli_config.json` automatically.

---

## 📁 Project Structure

```
RebornYoutubeSaver/
├── cli.py                   ← Entry point
├── cli_core/
│   ├── app.py               ← UI & application logic
│   ├── downloader.py        ← yt-dlp wrapper
│   ├── bypass.py            ← Rate-limit bypass engine
│   ├── config.py            ← Settings (cli_config.json)
│   ├── history.py           ← Download history
│   ├── display.py           ← Rich helpers & progress bars
│   └── styles.py            ← Colors, icons, ASCII art
├── cli_config.json          ← Auto-generated config
├── download_history.json    ← Auto-generated history
└── downloads/               ← Default output folder
```

---

## 🍪 Cookies (Age-restricted / Private videos)

**Option 1 — Browser export (recommended):**
1. Install the [cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) extension
2. Open YouTube, log in
3. Export cookies → save as `cookies.txt` in the project folder
4. The app detects it automatically

**Option 2 — Browser extraction (close browser first!):**
- Settings → `cookies_browser` → set to `chrome` / `firefox` / `edge`

---

## 📦 Dependencies

```
yt-dlp>=2025.01.15
rich>=13.7.0
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">

**Made with ❤️ by [EleRiSey Studio](https://github.com/yorikelesey-dot)**

[💬 Join our Discord](https://discord.gg/RcKBmrn2rj)

*If you find this useful, give it a ⭐ on GitHub!*

</div>
