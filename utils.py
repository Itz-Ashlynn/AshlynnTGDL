"""
utils.py  —  Shared helpers for AshlynnTGDL
"""

from sys import stdout, exit as sys_exit
from time import time
from os import system, name as os_name

from pyrogram import enums
from pyrogram.types import Message


# ─────────────────────────── Speed tracking ──────────────────────────────────

SPEED_DATA: dict = {}


# ─────────────────────────── Exit helper ─────────────────────────────────────

def wait() -> None:
    try:
        input("\nPress Enter to exit…")
    except KeyboardInterrupt:
        pass
    finally:
        sys_exit(0)


# ─────────────────────────── Progress bar ────────────────────────────────────

def progress(current: int, total: int, uid) -> None:
    """
    Pyrogram progress callback.
    Displays: [████░░░░] 42.0% | 3.21 MB/s | 12.3 MB / 29.1 MB | ETA: 5s
    """
    now      = time()
    bar_len  = 38

    if uid in SPEED_DATA:
        elapsed = now - SPEED_DATA[uid]["time"]
        speed   = (current - SPEED_DATA[uid]["bytes"]) / elapsed if elapsed > 0 else 0
    else:
        speed = 0

    SPEED_DATA[uid] = {"time": now, "bytes": current}

    pct  = (current / total * 100) if total > 0 else 0
    done = int(bar_len * current / total) if total > 0 else 0

    # ETA
    if speed > 0:
        secs = int((total - current) / speed)
        if secs >= 3600:
            eta = f"{secs // 3600}h {(secs % 3600) // 60}m"
        elif secs >= 60:
            eta = f"{secs // 60}m {secs % 60}s"
        else:
            eta = f"{secs}s"
    else:
        eta = "--"

    bar  = "█" * done + "░" * (bar_len - done)
    line = (
        f"\r  [{bar}] {pct:5.1f}%"
        f"  {convert_bytes(speed)}/s"
        f"  {convert_bytes(current)} / {convert_bytes(total)}"
        f"  ETA: {eta}   "
    )
    stdout.write(line)
    stdout.flush()


# ─────────────────────────── Byte formatter ──────────────────────────────────

def convert_bytes(size: float, precision: int = 2) -> str:
    if not size or size <= 0:
        return "0 B"
    suffixes = ["B", "KB", "MB", "GB", "TB"]
    idx = 0
    while size >= 1024 and idx < len(suffixes) - 1:
        size /= 1024.0
        idx  += 1
    return f"{size:.{precision}f} {suffixes[idx]}"


# ─────────────────────────── Media helpers ───────────────────────────────────

_MEDIA_ATTRS = (
    "audio", "document", "photo", "sticker",
    "animation", "video", "voice", "video_note",
)

_MEDIA_ICONS = {
    "Video":     "🎬",
    "Audio":     "🎵",
    "Document":  "📄",
    "Photo":     "🖼️",
    "Sticker":   "🎯",
    "Animation": "🎞️",
    "Voice":     "🎙️",
    "VideoNote": "📹",
}


def get_media_type(message: Message):
    """Return the first media object found in *message*, or None."""
    if isinstance(message, Message):
        for attr in _MEDIA_ATTRS:
            media = getattr(message, attr, None)
            if media is not None:
                return media
    return None


def _get_file_name(media) -> str:
    try:
        return media.file_name or media.file_unique_id
    except AttributeError:
        return getattr(media, "file_unique_id", "unknown")


def print_download_msg(media, count: int, total: int) -> None:
    """Print a one-line summary before downloading a media item."""
    mtype = media.__class__.__name__
    icon  = _MEDIA_ICONS.get(mtype, "📁")
    name  = _get_file_name(media)
    size  = (
        convert_bytes(media.file_size)
        if hasattr(media, "file_size") and media.file_size
        else "?"
    )
    print(f"\n  {icon} [{count}/{total}]  {name}  ({mtype}, {size})")


# ─────────────────────────── Usage examples ──────────────────────────────────

def print_examples() -> None:
    print("""
  ┌──────────────────────────────────────────────────────┐
  │                     📖  USAGE                        │
  │                                                      │
  │  Public channel / group:                             │
  │    https://t.me/channelname/1423                     │
  │                                                      │
  │  Private channel (use numeric ID):                   │
  │    https://t.me/c/1234567890/10                      │
  │                                                      │
  │  Range of messages:                                  │
  │    https://t.me/channelname/100-120                  │
  │    https://t.me/c/1234567890/100-120                 │
  │                                                      │
  │  With a custom sub-folder (after the link):          │
  │    https://t.me/channelname/1423 movies              │
  │    → downloads to  AshlynnTGDL/movies/               │
  │                                                      │
  │  No sub-folder → saves to  AshlynnTGDL/              │
  └──────────────────────────────────────────────────────┘""")


# ─────────────────────────── Config path ─────────────────────────────────────

configfile = "ashlynn_config.txt"


# ─────────────────────────── Banner ──────────────────────────────────────────

BANNER = r"""
  ╔═══════════════════════════════════════════════════════╗
  ║                                                       ║
  ║    _         _     _                 _____ ____ ____  ║
  ║   / \  ___  | |__ | |_   _ _ __    |_   _/ ___|  _ \  ║
  ║  / _ \/ __| | '_ \| | | | | '_ \    | || |  _| | | |  ║
  ║ / ___ \__ \ | | | | | |_| | | | |   | || |_| | |_| |  ║
  ║/_/   \_\___/|_| |_|_|\__, |_| |_|   |_| \____|____/   ║
  ║                       |___/           L               ║
  ║                                                       ║
  ║         AshlynnTGDL — Telegram Media Downloader       ║
  ║                       Version 2.0                     ║
  ╚═══════════════════════════════════════════════════════╝
"""
