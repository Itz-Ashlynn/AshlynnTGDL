import asyncio
import logging
import os
import re
import sys
from typing import Optional, Tuple
from urllib.parse import urlparse

# ── Ensure UTF-8 output on Windows terminals ──────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# ── Silence Pyrogram's internal "Retrying … due to: Request timed out" noise ─
logging.getLogger("pyrogram").setLevel(logging.CRITICAL)

from pyrogram import Client
from pyrogram.errors import (
    AuthKeyInvalid,
    AuthKeyUnregistered,
    BadRequest,
    FloodWait,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    SessionPasswordNeeded,
    SessionRevoked,
    Unauthorized,
    UserDeactivated,
    UserDeactivatedBan,
)
from pyrogram.types import Message, User

from utils import (
    BANNER,
    configfile,
    convert_bytes,
    create_download_bar,
    get_media_type,
    print_download_msg,
    print_examples,
    reset_config,
    sanitize_filename,
    _get_file_name,
)

BASE_FOLDER = "AshlynnTGDL"

# ─────────────────────────── Throttle-safe delay config ──────────────────────
DELAY_BETWEEN_FILES   = 1.5   # seconds between every file (keeps speed steady)
DELAY_EVERY_10_FILES  = 6     # extra seconds after every 10th file
DELAY_EVERY_50_FILES  = 20    # extra seconds after every 50th file (long sessions)
DOWNLOAD_RETRIES      = 2     # retry a failed download this many times before skipping

# ─────────────────────────── Custom Auth Exception ───────────────────────────
class AuthExpiredError(Exception):
    """Raised when Telegram authorization key is expired or unregistered."""
    pass

AUTH_ERRORS = (
    AuthKeyUnregistered,
    AuthKeyInvalid,
    SessionRevoked,
    Unauthorized,
    UserDeactivated,
    UserDeactivatedBan,
    AuthExpiredError,
)

def is_auth_error(exc: Exception) -> bool:
    """Check if an exception is related to session expiration or unregistered key."""
    if isinstance(exc, AUTH_ERRORS):
        return True
    err_str = str(exc).upper()
    return "AUTH_KEY_UNREGISTERED" in err_str or "401" in err_str or "SESSION_REVOKED" in err_str or "USER_DEACTIVATED" in err_str


# ─────────────────────────── Config helpers ──────────────────────────────────

def load_config() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Load API ID, API HASH, and session string from config file."""
    if not os.path.exists(configfile):
        return None, None, None
    with open(configfile, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.readlines()]
    api_id    = lines[0] if len(lines) > 0 and lines[0]    else None
    api_hash  = lines[1] if len(lines) > 1 and lines[1]  else None
    session   = lines[2] if len(lines) > 2 and lines[2]  else None
    return api_id, api_hash, session


def save_config(api_id: str, api_hash: str, session: str) -> None:
    """Persist credentials to config file with restricted POSIX file permissions."""
    with open(configfile, "w", encoding="utf-8") as f:
        f.write(f"{api_id.strip()}\n{api_hash.strip()}\n{session.strip()}\n")
    if os.name != "nt":
        try:
            os.chmod(configfile, 0o600)
        except Exception:
            pass


# ─────────────────────────── Login helpers ───────────────────────────────────

async def phone_login(api_id: str, api_hash: str) -> str:
    """Full interactive phone → OTP → (optional 2FA) login. Returns session string."""
    print("\n  📱 Phone Number Login")
    print("  ─────────────────────────────────────")
    print("  Format: +CountryCodeNumber (e.g. +919876543210)")
    phone = input("  Phone : ").strip()
    if phone.lower() in ("q", "cancel", "exit"):
        raise KeyboardInterrupt("Login cancelled by user.")

    client = Client(
        "ashlynn_temp_auth",
        api_id=int(api_id),
        api_hash=api_hash,
        in_memory=True,
    )
    await client.connect()

    try:
        sent = await client.send_code(phone)
        print(f"\n  ✅ OTP sent to {phone}")

        # ── OTP loop ──────────────────────────────────────────────────────────
        signed_in = False
        while not signed_in:
            code = input("  OTP Code (or 'q' to cancel): ").strip()
            if code.lower() in ("q", "cancel", "exit"):
                raise KeyboardInterrupt("Login cancelled by user.")
            try:
                await client.sign_in(phone, sent.phone_code_hash, code)
                signed_in = True
            except PhoneCodeInvalid:
                print("  ❌ Invalid code — try again.")
            except PhoneCodeExpired:
                print("  ❌ Code expired — re-sending…")
                sent = await client.send_code(phone)
            except SessionPasswordNeeded:
                # ── 2FA loop ──────────────────────────────────────────────────
                print("\n  🔒 Two-Factor Authentication required.")
                while True:
                    pwd = input("  2FA Password (or 'q' to cancel): ").strip()
                    if pwd.lower() in ("q", "cancel", "exit"):
                        raise KeyboardInterrupt("Login cancelled by user.")
                    try:
                        await client.check_password(pwd)
                        signed_in = True
                        break
                    except BadRequest:
                        print("  ❌ Wrong password — try again.")

        me = await client.get_me()
        full_name = f"{me.first_name}{(' ' + me.last_name) if me.last_name else ''}"
        print(f"\n  ✅ Logged in as: {full_name} ({me.id})")

        session_string = await client.export_session_string()
        return session_string

    except Exception as exc:
        print(f"\n  ❌ Login failed: {exc}")
        raise exc
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def do_login(api_id: str, api_hash: str) -> str:
    """Ask user to choose login method and return a valid session string."""
    while True:
        print("\n  🔐 Choose Login Method:")
        print("     1. Session String  (use an existing string)")
        print("     2. Phone + OTP     (generates a new session)")

        while True:
            choice = input("\n  Enter choice (1 / 2): ").strip()
            if choice in ("1", "2"):
                break
            print("  ❌ Please enter 1 or 2")

        if choice == "1":
            ss = input("  Session String : ").strip()
            if not ss:
                print("  ❌ Session string cannot be empty.")
                continue
            print("  🔄 Validating session…")
            tmp = Client(
                "ashlynn_validate",
                api_id=int(api_id),
                api_hash=api_hash,
                session_string=ss,
                in_memory=True,
            )
            try:
                await tmp.start()
                me = await tmp.get_me()
                full_name = f"{me.first_name}{(' ' + me.last_name) if me.last_name else ''}"
                print(f"  ✅ Valid! Logged in as: {full_name} ({me.id})")
                await tmp.stop()
                return ss
            except Exception as exc:
                print(f"  ❌ Session invalid or expired ({exc}). Please try again.")
                continue
        else:
            try:
                return await phone_login(api_id, api_hash)
            except Exception:
                print("  🔄 Let's try authorization again.")


async def get_credentials() -> Tuple[str, str, str]:
    """Return (api_id, api_hash, session_string), prompting as needed."""
    api_id, api_hash, session = load_config()
    needs_save = False

    if not api_id or not api_hash:
        print("\n  " + "═" * 52)
        print("  🛠️   FIRST TIME SETUP — my.telegram.org credentials")
        print("  " + "═" * 52)
        api_id   = input("  API ID   : ").strip()
        api_hash = input("  API HASH : ").strip()
        needs_save = True

    if not session:
        session = await do_login(api_id, api_hash)
        needs_save = True

    if needs_save:
        save_config(api_id, api_hash, session)
        print(f"\n  💾 Credentials saved to '{configfile}' — auto-login next time!")

    return api_id, api_hash, session


# ─────────────────────────── Link / path helpers ─────────────────────────────

def parse_replace_param(text: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Extract replace="find"="with" from raw input text."""
    pattern = re.compile(r'replace="([^"]*)"="([^"]*)"')
    m = pattern.search(text)
    if m:
        find_str  = m.group(1)
        with_str  = m.group(2)
        clean     = (text[:m.start()] + text[m.end():]).strip()
        return clean, find_str, with_str
    return text, None, None


def apply_filename_replace(filename: str, find: str, replace_with: str) -> str:
    """Replace find inside the filename stem only and sanitize output filename."""
    stem, ext = os.path.splitext(filename)
    new_stem  = stem.replace(find, replace_with)
    sanitized_stem = sanitize_filename(new_stem)
    return (sanitized_stem + ext) if ext else sanitized_stem


def parse_user_input(text: str) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    """Parse 'url [folder] [replace="find"="with"]' input."""
    text, find, replace_with = parse_replace_param(text)
    parts  = text.strip().split(None, 1)
    url    = parts[0] if parts else ""
    folder = parts[1].strip() if len(parts) > 1 else None
    return url, folder, find, replace_with


def parse_telegram_link(link: str):
    """Parse a t.me link → (chat_id, from_id, to_id) or (None, None, None)."""
    if not link or "t.me/" not in link:
        return None, None, None

    parsed = urlparse(link)
    path_parts = [p for p in parsed.path.strip("/").split("/") if p]
    if not path_parts:
        return None, None, None

    raw_ids = path_parts[-1].split("-")
    try:
        from_id = int(raw_ids[0].strip())
        to_id   = int(raw_ids[1].strip()) if len(raw_ids) > 1 else from_id
    except (ValueError, IndexError):
        return None, None, None

    if path_parts[0] == "c" and len(path_parts) >= 3:
        try:
            chat_id = int("-100" + path_parts[1])
        except ValueError:
            return None, None, None
    elif path_parts[0] != "c":
        chat_id = path_parts[0]
    else:
        return None, None, None

    return chat_id, from_id, to_id


def make_download_folder(subfolder: Optional[str]) -> str:
    """Create and return the target download directory safely."""
    if subfolder:
        clean_parts = [sanitize_filename(p) for p in subfolder.replace("\\", "/").split("/") if p and p != ".."]
        safe_subfolder = os.path.join(*clean_parts) if clean_parts else ""
        path = os.path.join(BASE_FOLDER, safe_subfolder) if safe_subfolder else BASE_FOLDER
    else:
        path = BASE_FOLDER
    os.makedirs(path, exist_ok=True)
    return path


# ─────────────────────────── Download engine ────────────────────────────────

async def _download_with_retry(
    client: Client,
    msg: Message,
    dl_path: str,
    idx: int,
    total: int,
    target_filename: Optional[str] = None,
) -> Optional[str]:
    """
    Attempt to download a media message up to DOWNLOAD_RETRIES+1 times.
    Uses alive-progress with byte scaling (MB/s speed) for smooth UI.
    """
    file_name_param = (
        os.path.join(dl_path, target_filename)
        if target_filename
        else dl_path + os.sep
    )

    media = get_media_type(msg)
    total_bytes = getattr(media, "file_size", 0) if media else 0

    with create_download_bar(total_bytes, f"  [{idx}/{total}]") as bar:
        for attempt in range(1, DOWNLOAD_RETRIES + 2):
            try:
                def _progress(current, total_b):
                    if total_b > 0:
                        bar(current / total_b)
                    else:
                        bar(0)

                file_path = await client.download_media(
                    msg,
                    file_name=file_name_param,
                    progress=_progress,
                )
                bar(1.0)
                return file_path

            except FloodWait as fw:
                print(f"  ⏳ [{idx}/{total}] Rate-limited — waiting {fw.value}s…")
                await asyncio.sleep(fw.value)

            except ValueError as exc:
                if "doesn't contain any downloadable media" not in str(exc):
                    print(f"  ⚠️  [{idx}/{total}] {exc}")
                return None

            except Exception as exc:
                if is_auth_error(exc):
                    raise AuthExpiredError(f"Authorization key expired: {exc}")

                if attempt <= DOWNLOAD_RETRIES:
                    wait = attempt * 3
                    print(
                        f"  ⚠️  [{idx}/{total}] Attempt {attempt} failed: {exc}"
                        f" — retrying in {wait}s…"
                    )
                    await asyncio.sleep(wait)
                else:
                    print(f"  ❌ [{idx}/{total}] Download failed after {DOWNLOAD_RETRIES + 1} attempts: {exc}")
                    return None
    return None


async def download_range(
    client: Client,
    chat_id,
    from_id: int,
    to_id: int,
    dl_path: str,
    find: Optional[str] = None,
    replace_with: Optional[str] = None,
) -> None:
    """Download every message in [from_id, to_id] to dl_path."""
    total = to_id - from_id + 1
    stats = {"media": 0, "text": 0, "skipped": 0}

    print(f"\n  📥 Fetching {total} message(s)…")
    print("  " + "─" * 52)

    for msg_id in range(from_id, to_id + 1):
        idx = msg_id - from_id + 1

        try:
            msg: Message = await client.get_messages(chat_id, msg_id)
        except FloodWait as fw:
            print(f"\n  ⏳ Flood wait — sleeping {fw.value}s…")
            await asyncio.sleep(fw.value)
            try:
                msg = await client.get_messages(chat_id, msg_id)
            except Exception as e2:
                if is_auth_error(e2):
                    raise AuthExpiredError(str(e2))
                print(f"\n  ❌ Still failed after wait: {e2}")
                stats["skipped"] += 1
                continue
        except Exception as exc:
            if is_auth_error(exc):
                raise AuthExpiredError(str(exc))
            print(f"\n  ❌ Error fetching #{msg_id}: {exc}")
            stats["skipped"] += 1
            continue

        if msg.empty:
            print(f"\n  ⚠️  [{idx}/{total}] Message #{msg_id} not found — skipped")
            stats["skipped"] += 1
            continue

        media = get_media_type(msg)

        if media:
            print_download_msg(media, idx, total)

            target_filename: Optional[str] = None
            if find is not None:
                raw_name = _get_file_name(media)
                renamed  = apply_filename_replace(raw_name, find, replace_with or "")
                if renamed != raw_name:
                    target_filename = renamed
                    print(f"  ✏️  Rename : {raw_name}\n           → {renamed}")

            file_path = await _download_with_retry(
                client, msg, dl_path, idx, total,
                target_filename=target_filename,
            )

            if file_path:
                print(f"  ✅ Saved  →  {os.path.basename(file_path)}")
                stats["media"] += 1
            else:
                stats["skipped"] += 1

            completed = stats["media"]

            if completed > 0 and completed % 50 == 0:
                print(
                    f"\n  🛡️  [{completed} files done] Safety pause {DELAY_EVERY_50_FILES}s "
                    f"to protect your account…"
                )
                await asyncio.sleep(DELAY_EVERY_50_FILES)

            elif completed > 0 and completed % 10 == 0:
                print(
                    f"\n  ⏸️  [{completed} files done] Quick cooldown {DELAY_EVERY_10_FILES}s "
                    f"to keep speed steady…"
                )
                await asyncio.sleep(DELAY_EVERY_10_FILES)

            else:
                await asyncio.sleep(DELAY_BETWEEN_FILES)

        else:
            text = (msg.text or msg.caption or "").strip()
            if text:
                chat_str = str(chat_id)
                if chat_str.startswith("-100"):
                    chat_part = chat_str[4:]
                elif chat_str.startswith("-"):
                    chat_part = chat_str[1:]
                else:
                    chat_part = chat_str
                chat_part = chat_part[-10:]
                fname = f"{chat_part}-{msg.id}.txt"
                fpath = os.path.join(dl_path, fname)
                with open(fpath, "w", encoding="utf-8") as fh:
                    fh.write(text)
                print(f"\n  📝 [{idx}/{total}] Text saved  →  {fname}")
                stats["text"] += 1
            else:
                print(f"\n  ⏭️  [{idx}/{total}] Empty / unsupported — skipped")
                stats["skipped"] += 1

    print(f"\n  {'─' * 52}")
    print(
        f"  📊 Done!  "
        f"🎬 {stats['media']} media  "
        f"📝 {stats['text']} text  "
        f"⚠️  {stats['skipped']} skipped"
    )
    print(f"  📁 Saved to : {os.path.abspath(dl_path)}")


# ─────────────────────────── Entry point ─────────────────────────────────────

async def main() -> None:
    print(BANNER)

    while True:
        try:
            api_id, api_hash, session = await get_credentials()
        except KeyboardInterrupt:
            print("\n\n  Goodbye! 👋")
            return

        print("\n  🔄 Connecting to Telegram…")
        client = Client(
            "AshlynnTGDL",
            api_id=int(api_id),
            api_hash=api_hash.strip(),
            session_string=session.strip(),
            in_memory=True,
            workers=8,
            no_updates=True,
            max_concurrent_transmissions=4,
        )

        try:
            await client.start()
            me: User = await client.get_me()
            full_name = f"{me.first_name}{(' ' + me.last_name) if me.last_name else ''}"
            username  = f" @{me.username}" if me.username else ""

            print(f"\n  ✅ Connected as : {full_name}{username}  [ID: {me.id}]")
            print(f"  📁 Base folder  : {os.path.abspath(BASE_FOLDER)}")
            print_examples()

            while True:
                try:
                    print()
                    print("  " + "═" * 52)
                    user_input = input(
                        "  🔗 Link [folder] [replace=\"find\"=\"with\"]  |  q = quit\n"
                        "  > "
                    ).strip()

                    if not user_input or user_input.lower() in ("q", "quit", "exit"):
                        break

                    url, folder, find, replace_with = parse_user_input(user_input)

                    if url.startswith("t.me/"):
                        url = "https://" + url
                    elif url.startswith("telegram.me/"):
                        url = "https://t.me/" + url[12:]
                    elif url.startswith("https://telegram.me/"):
                        url = "https://t.me/" + url[20:]
                    elif url.startswith("http://t.me/"):
                        url = "https://t.me/" + url[12:]

                    if not url.startswith("https://t.me/"):
                        print("  ❌ Not a valid Telegram link (must start with https://t.me/ or t.me/)")
                        continue

                    chat_id, from_id, to_id = parse_telegram_link(url)
                    if chat_id is None:
                        print("  ❌ Could not parse link. Check the format.")
                        continue

                    dl_path      = make_download_folder(folder)
                    folder_label = f"AshlynnTGDL/{folder}" if folder else "AshlynnTGDL"

                    print(f"\n  📂 Folder   : {folder_label}")
                    print(f"  💬 Chat     : {chat_id}")
                    print(
                        f"  📨 Messages : "
                        f"{from_id}"
                        f"{'  →  ' + str(to_id) if to_id != from_id else ''}"
                        f"  ({to_id - from_id + 1} total)"
                    )

                    if find:
                        rw_display = f'"{replace_with}"' if replace_with else '(remove)'
                        print(f"  ✏️  Replace : \"{find}\" → {rw_display}")

                    await download_range(
                        client, chat_id, from_id, to_id, dl_path,
                        find=find, replace_with=replace_with,
                    )

                    again = input("\n  🔄 Download more? (y / n): ").strip().lower()
                    if again != "y":
                        break

                except AuthExpiredError as exc:
                    raise exc
                except KeyboardInterrupt:
                    print("\n\n  ⚠️  Interrupted.")
                    break

            # Exit inner loop normally (user chose quit or no more downloads)
            await client.stop()
            print("\n  👋 Goodbye from AshlynnTGDL!")
            break

        except Exception as exc:
            try:
                await client.stop()
            except Exception:
                pass

            if is_auth_error(exc):
                print(f"\n  🔑 Session Expired or Key Invalid: {exc}")
                print("  ⚠️  Your session string / authorization key is no longer registered with Telegram.")
                reset_config()
                print("  🔄 Please log in again to generate fresh credentials.\n")
                # Loop continues and calls get_credentials(), which auto-triggers clean re-login!
                continue
            else:
                print(f"\n  ❌ Fatal error: {exc}")
                print(f"  💡 Tip: Delete '{configfile}' to reset your credentials.")
                break


if __name__ == "__main__":
    asyncio.run(main())
