import asyncio
import logging
import os
import re
import sys
from typing import Optional, Tuple
from uuid import uuid4

# ── Silence Pyrogram's internal "Retrying … due to: Request timed out" noise ─
logging.getLogger("pyrogram").setLevel(logging.CRITICAL)

from pyrogram import Client
from pyrogram.errors import (
    BadRequest,
    FloodWait,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    SessionPasswordNeeded,
)
from pyrogram.types import Message, User

# We'll assume these exist in utils.py
try:
    from utils import (
        BANNER,
        SPEED_DATA,
        configfile,
        convert_bytes,
        get_media_type,
        print_download_msg,
        print_examples,
        progress,
    )
except ImportError:
    # Minimal mock for research purposes
    BANNER = "AshlynnTGDL"
    SPEED_DATA = {}
    configfile = "config.txt"
    def convert_bytes(n): return str(n)
    def get_media_type(msg): return msg.media
    def print_download_msg(*args): pass
    def print_examples(): pass
    async def progress(*args): pass

BASE_FOLDER = "AshlynnTGDL"
TARGET_CHANNEL_ID = -1003885052148  # Target channel for uploads

# ─────────────────────────── Throttle-safe delay config ──────────────────────
DELAY_BETWEEN_FILES   = 1.5   
DELAY_EVERY_10_FILES  = 6     
DELAY_EVERY_50_FILES  = 20    
DOWNLOAD_RETRIES      = 2     

# ─────────────────────────── Config helpers ──────────────────────────────────

def load_config() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    if not os.path.exists(configfile):
        return None, None, None
    with open(configfile, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.readlines()]
    api_id    = lines[0] if len(lines) > 0 and lines[0]    else None
    api_hash  = lines[1] if len(lines) > 1 and lines[1]  else None
    session   = lines[2] if len(lines) > 2 and lines[2]  else None
    return api_id, api_hash, session


def save_config(api_id: str, api_hash: str, session: str) -> None:
    with open(configfile, "w", encoding="utf-8") as f:
        f.write(f"{api_id.strip()}\n{api_hash.strip()}\n{session.strip()}\n")


# ─────────────────────────── Login helpers ───────────────────────────────────

async def phone_login(api_id: str, api_hash: str) -> str:
    print("\n  📱 Phone Number Login")
    print("  ─────────────────────────────────────")
    print("  Format: +CountryCodeNumber (e.g. +919876543210)")
    phone = input("  Phone : ").strip()

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

        signed_in = False
        while not signed_in:
            code = input("  OTP Code : ").strip()
            try:
                await client.sign_in(phone, sent.phone_code_hash, code)
                signed_in = True
            except PhoneCodeInvalid:
                print("  ❌ Invalid code — try again.")
            except PhoneCodeExpired:
                print("  ❌ Code expired — re-sending…")
                sent = await client.send_code(phone)
            except SessionPasswordNeeded:
                print("\n  🔒 Two-Factor Authentication required.")
                while True:
                    pwd = input("  2FA Password : ").strip()
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
        sys.exit(1)
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def do_login(api_id: str, api_hash: str) -> str:
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
        except Exception as exc:
            print(f"  ❌ Session invalid: {exc}")
            sys.exit(1)
        return ss
    else:
        return await phone_login(api_id, api_hash)


async def get_credentials() -> Tuple[str, str, str]:
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


# ─────────────────────────── Filename rename helpers ─────────────────────────

def parse_replace_param(text: str) -> Tuple[str, Optional[str], Optional[str]]:
    pattern = re.compile(r'replace="([^"]*)"="([^"]*)"')
    m = pattern.search(text)
    if m:
        find_str  = m.group(1)
        with_str  = m.group(2)
        clean     = (text[:m.start()] + text[m.end():]).strip()
        return clean, find_str, with_str
    return text, None, None


def apply_filename_replace(filename: str, find: str, replace_with: str) -> str:
    stem, ext = os.path.splitext(filename)
    new_stem  = stem.replace(find, replace_with)
    return new_stem + ext


def parse_user_input(text: str) -> Tuple[str, Optional[str], Optional[str], Optional[str]]:
    text, find, replace_with = parse_replace_param(text)
    parts  = text.strip().split(None, 1)
    url    = parts[0] if parts else ""
    folder = parts[1].strip() if len(parts) > 1 else None
    return url, folder, find, replace_with


def parse_telegram_link(link: str):
    if not link.startswith("https://t.me/"):
        return None, None, None

    parts   = link.split("/")
    raw_ids = parts[-1].replace("?single", "").split("-")

    try:
        from_id = int(raw_ids[0].strip())
        to_id   = int(raw_ids[1].strip()) if len(raw_ids) > 1 else from_id
    except (ValueError, IndexError):
        return None, None, None

    if len(parts) > 4 and parts[3] == "c":
        chat_id = int("-100" + parts[4])
    else:
        chat_id = parts[3]   

    return chat_id, from_id, to_id


def make_download_folder(subfolder: Optional[str]) -> str:
    if subfolder:
        safe = subfolder.replace("..", "_").replace("/", "_").replace("\\", "_")
        path = os.path.join(BASE_FOLDER, safe)
    else:
        path = BASE_FOLDER
    os.makedirs(path, exist_ok=True)
    return path


# ─────────────────────────── Download engine ────────────────────────────────

async def _download_with_retry(
    client: Client,
    msg: Message,
    dl_path: str,
    uid,
    idx: int,
    total: int,
    target_filename: Optional[str] = None,
) -> Optional[str]:
    file_name_param = (
        os.path.join(dl_path, target_filename)
        if target_filename
        else dl_path + os.sep       
    )
    for attempt in range(1, DOWNLOAD_RETRIES + 2):
        try:
            file_path = await client.download_media(
                msg,
                file_name=file_name_param,
                progress=progress,
                progress_args=(uid,),
            )
            SPEED_DATA.pop(uid, None)
            return file_path

        except FloodWait as fw:
            SPEED_DATA.pop(uid, None)
            print(f"\n  ⏳ [{idx}/{total}] Rate-limited — waiting {fw.value}s…")
            await asyncio.sleep(fw.value)

        except ValueError as exc:
            SPEED_DATA.pop(uid, None)
            if "doesn't contain any downloadable media" not in str(exc):
                print(f"\n  ⚠️  [{idx}/{total}] {exc}")
            return None  

        except Exception as exc:
            SPEED_DATA.pop(uid, None)
            if attempt <= DOWNLOAD_RETRIES:
                wait = attempt * 3          
                print(
                    f"\n  ⚠️  [{idx}/{total}] Attempt {attempt} failed: {exc}"
                    f" — retrying in {wait}s…"
                )
                await asyncio.sleep(wait)
            else:
                print(f"\n  ❌ [{idx}/{total}] Download failed after {DOWNLOAD_RETRIES + 1} attempts: {exc}")
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
    total = to_id - from_id + 1
    stats = {"media": 0, "text": 0, "skipped": 0}

    print(f"\n  📥 Fetching {total} message(s)…")
    print("  " + "─" * 52)

    for msg_id in range(from_id, to_id + 1):
        idx = msg_id - from_id + 1
        uid = uuid4()

        try:
            msg: Message = await client.get_messages(chat_id, msg_id)
        except FloodWait as fw:
            print(f"\n  ⏳ Flood wait — sleeping {fw.value}s…")
            await asyncio.sleep(fw.value)
            try:
                msg = await client.get_messages(chat_id, msg_id)
            except Exception as e2:
                print(f"\n  ❌ Still failed after wait: {e2}")
                stats["skipped"] += 1
                continue
        except Exception as exc:
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
                try:
                    from utils import _get_file_name
                    raw_name     = _get_file_name(media)
                    renamed      = apply_filename_replace(raw_name, find, replace_with or "")
                    if renamed != raw_name:
                        target_filename = renamed
                        print(f"  ✏️  Rename : {raw_name}\n           → {renamed}")
                except ImportError:
                    pass

            file_path = await _download_with_retry(
                client, msg, dl_path, uid, idx, total,
                target_filename=target_filename,
            )

            if file_path:
                print(f"\n  ✅ Saved  →  {os.path.basename(file_path)}")
                stats["media"] += 1

                # ── Upload to target channel and Cleanup ─────────────────────
                try:
                    print(f"  📤 Uploading to channel...")
                    caption = msg.caption or ""
                    
                    # Determine right method based on media type
                    if msg.video:
                        await client.send_video(TARGET_CHANNEL_ID, video=file_path, caption=caption)
                    elif msg.photo:
                        await client.send_photo(TARGET_CHANNEL_ID, photo=file_path, caption=caption)
                    elif msg.audio:
                        await client.send_audio(TARGET_CHANNEL_ID, audio=file_path, caption=caption)
                    elif msg.voice:
                        await client.send_voice(TARGET_CHANNEL_ID, voice=file_path, caption=caption)
                    elif msg.animation:
                        await client.send_animation(TARGET_CHANNEL_ID, animation=file_path, caption=caption)
                    else:
                        await client.send_document(TARGET_CHANNEL_ID, document=file_path, caption=caption)
                    
                    print(f"  ✨ Uploaded successfully!")
                    
                    # Delete local file after upload
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"  🗑️  Local file deleted.")
                    
                    # Delete source message
                    try:
                        await client.delete_messages(chat_id, msg_id)
                        print(f"  ❌ Source message deleted.")
                    except Exception as e:
                        print(f"  ⚠️  Could not delete source: {e}")

                except Exception as e:
                    print(f"  ⚠️  Upload failed: {e}. Local file kept.")
            else:
                stats["skipped"] += 1

            completed = stats["media"]

            if completed > 0 and completed % 50 == 0:
                await asyncio.sleep(DELAY_EVERY_50_FILES)
            elif completed > 0 and completed % 10 == 0:
                await asyncio.sleep(DELAY_EVERY_10_FILES)
            else:
                await asyncio.sleep(DELAY_BETWEEN_FILES)

        else:
            text = (msg.text or msg.caption or "").strip()
            if text:
                chat_part = str(chat_id).lstrip("-").lstrip("100")[-10:]
                fname = f"{chat_part}-{msg.id}.txt"
                fpath = os.path.join(dl_path, fname)
                with open(fpath, "w", encoding="utf-8") as fh:
                    fh.write(text)
                print(f"\n  📝 [{idx}/{total}] Text saved  →  {fname}")
                stats["text"] += 1

                # ── Send to target channel and Cleanup ─────────────────────
                try:
                    await client.send_message(TARGET_CHANNEL_ID, text)
                    print(f"  📤 Text sent to channel.")
                    
                    # Delete local txt file
                    if os.path.exists(fpath):
                        os.remove(fpath)
                    
                    # Delete source message
                    try:
                        await client.delete_messages(chat_id, msg_id)
                        print(f"  ❌ Source message deleted.")
                    except Exception as e:
                        print(f"  ⚠️  Could not delete source: {e}")
                except Exception as e:
                    print(f"  ⚠️  Failed to send text to channel: {e}")
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
        full_name  = f"{me.first_name}{(' ' + me.last_name) if me.last_name else ''}"
        username   = f" @{me.username}" if me.username else ""

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

                if not url.startswith("https://t.me/"):
                    print("  ❌ Not a valid Telegram link (must start with https://t.me/)")
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

            except KeyboardInterrupt:
                print("\n\n  ⚠️  Interrupted.")
                break

    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"\n  ❌ Fatal error: {exc}")
        print(f"  💡 Tip: Delete '{configfile}' to reset your credentials.")
    finally:
        try:
            await client.stop()
        except Exception:
            pass
        print("\n  👋 Goodbye from AshlynnTGDL!")


if __name__ == "__main__":
    asyncio.run(main())
