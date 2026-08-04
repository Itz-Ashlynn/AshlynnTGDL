"""
utils.py  —  Shared helpers for AshlynnTGDL
"""

import os
import re
import sys
from sys import exit as sys_exit

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from alive_progress import alive_bar
from pyrogram import enums
from pyrogram.types import Message


# ─────────────────────────── Exit helper ─────────────────────────────────────

def wait() -> None:
    try:
        input("\nPress Enter to exit…")
    except KeyboardInterrupt:
        pass
    finally:
        sys_exit(0)


# ─────────────────────────── Config management ───────────────────────────────

configfile = "ashlynn_config.txt"


def reset_config() -> None:
    """Delete ashlynn_config.txt if it exists to allow re-login."""
    if os.path.exists(configfile):
        try:
            os.remove(configfile)
            print(f"  🗑️  Old credentials file '{configfile}' deleted.")
        except Exception as exc:
            print(f"  ⚠️  Could not delete '{configfile}': {exc}")


# ─────────────────────────── Alive Progress Bar ──────────────────────────────

def create_download_bar(total_bytes: int = 0, title: str = "Downloading"):
    """Return a configured alive_bar context manager for file downloads.

    When total_bytes > 0, unit='B' and scale='SI' are passed so alive-progress
    displays real-time throughput in MB/s (or KB/s) along with total size and ETA.
    """
    kwargs = dict(
        manual=True,
        theme="smooth",
        title=title,
        force_tty=True,
    )
    if total_bytes and total_bytes > 0:
        kwargs.update(total=int(total_bytes), unit="B", scale="SI")
    return alive_bar(**kwargs)


# ─────────────────────────── Byte formatter ──────────────────────────────────

def convert_bytes(size: float, precision: int = 2) -> str:
    if not size or size <= 0:
        return "0 B"
    suffixes = ["B", "KB", "MB", "GB", "TB"]
    idx = 0
    while size >= 1024 and idx < len(suffixes) - 1:
        size /= 1024.0
        idx += 1
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


def sanitize_filename(name: str) -> str:
    """Sanitize filename/folder name by removing OS invalid characters (<>:"/\\|?*) and path traversal elements."""
    if not name:
        return "unnamed"
    # Replace invalid OS characters with underscores
    clean = re.sub(r'[<>:"/\\|?*]', '_', str(name))
    # Strip leading/trailing whitespace and dots
    clean = clean.strip(" .")
    return clean or "unnamed"


def _get_file_name(media) -> str:
    try:
        raw_name = media.file_name or media.file_unique_id
    except AttributeError:
        raw_name = getattr(media, "file_unique_id", "unknown")

    stem, ext = os.path.splitext(raw_name)
    sanitized_stem = sanitize_filename(stem)
    return sanitized_stem + ext if ext else sanitized_stem


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
