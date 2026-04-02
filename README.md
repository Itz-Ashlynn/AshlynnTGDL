<div align="center">

```
    _         _     _                 _____ ____ ____  _
   / \   ___ | |__ | |_   _ _ __    |_   _/ ___|  _ \| |
  / _ \ / __|| '_ \| | | | | '_ \    | || |  _| | | | |
 / ___ \__ \| | | | | |_| | | | |   | || |_| | |_| | |___
/_/   \_\___/|_| |_|_|\__, |_| |_|   |_| \____|____/|_____|
                       |___/           L
```

# AshlynnTGDL
### Telegram Media Fetch Tool — Version 2.0

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Kurigram](https://img.shields.io/badge/Powered%20by-Kurigram-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://pypi.org/project/kurigram/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Telegram](https://img.shields.io/badge/Channel-Ashlynn_Repository-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://t.me/Ashlynn_Repository)
[![GitHub](https://img.shields.io/badge/GitHub-AshlynnTGDL-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/Itz-Ashlynn/AshlynnTGDL)

**A client-based Telegram media fetch tool — save media from chats and channels you are a member of, directly to your local machine.**

*Made with ❤️ by [Aarabh](https://t.me/Ashlynn_Repository)*

</div>

---

> [!CAUTION]
> ## ⚠️ Legal Disclaimer & Responsible Use
>
> **AshlynnTGDL is intended strictly for educational and personal use.**
>
> - This tool operates using **your own Telegram account and your own API credentials** obtained from [my.telegram.org](https://my.telegram.org). It does not exploit any vulnerability or undocumented API.
> - **You are solely responsible** for how you use this tool and for ensuring your usage complies with [Telegram's Terms of Service](https://telegram.org/tos) and the laws of your jurisdiction.
> - **Only use this tool on chats, channels, or groups where you are a legitimate member** and have the right to access and save the content being fetched.
> - The author does **not** encourage, promote, or support unauthorized access to content, distribution of copyrighted material, or any activity that violates third-party rights.
> - **Downloading large volumes of media in a short period may result in rate limiting or account restrictions by Telegram.** Use responsibly and respect Telegram's rate limits.
> - By using this tool, you agree that **the author bears no liability** for any consequences, including account suspension, data loss, or legal issues arising from your use.

---

## ✨ Features

| Feature | Details |
|---------|---------|
| 🔐 **Flexible Login** | Session String **or** Phone + OTP + 2FA — your choice |
| 💾 **Auto Session Save** | Credentials stored once; auto-login on every future run |
| 📁 **Smart Folder System** | All downloads inside `AshlynnTGDL/`; create named sub-folders per batch |
| 🎬 **All Media Types** | Videos, Audios, Photos, Documents, Stickers, Animations, Voice notes, Video notes |
| 📝 **Text Backup** | Text-only messages saved as `.txt` files |
| 📊 **Live Progress Bar** | Real-time speed, percentage, data transferred, and ETA |
| ⚡ **Async Engine** | Fully `asyncio`-powered via Kurigram for fast, non-blocking fetching |
| 🔁 **FloodWait Handling** | Auto-detects Telegram rate limits and pauses before retrying |
| ✏️ **Filename Renaming** | Strip or replace branding text from filenames with `replace=` |
| 🛡️ **Account-safe Delays** | Smart cooldowns between files to prevent rate-limit throttling |
| 🖥️ **Cross-Platform** | Works on Windows, Linux, and macOS |

---

## 📋 Requirements

- Python **3.9 or higher**
- A Telegram account *(must be a member of any chat/channel you intend to fetch from)*
- API credentials from [my.telegram.org](https://my.telegram.org)

---

## 🚀 Installation

### 1 · Clone the repository

```bash
git clone https://github.com/Itz-Ashlynn/AshlynnTGDL.git
cd AshlynnTGDL
```

### 2 · Install dependencies

```bash
pip install -r requirements.txt
```

> `requirements.txt` installs:
> - `kurigram` — actively-maintained Pyrogram fork (MTProto client)
> - `PyroTgCrypto` — native C extension for faster crypto operations

### 3 · Run

```bash
python ashlynntgdl.py
```

---

## 🔐 First-Time Login

On the very first run you will be guided through a one-time setup:

```
  ════════════════════════════════════════════════════
  🛠️   FIRST TIME SETUP — my.telegram.org credentials
  ════════════════════════════════════════════════════
  API ID   : <your api id>
  API HASH : <your api hash>
```

> Get your **API ID** and **API HASH** from 👉 [my.telegram.org](https://my.telegram.org)  
> These are personal credentials tied to your own Telegram account.

### Login Methods

```
  🔐 Choose Login Method:
     1. Session String  (use an existing string)
     2. Phone + OTP     (generates a new session)
```

#### Method 1 — Session String
Paste an existing Pyrogram-compatible session string.
The string is validated live before being saved.

#### Method 2 — Phone + OTP

```
  📱 Phone Number Login
  Format: +CountryCodeNumber (e.g. +919876543210)
  Phone : +1xxxxxxxxxx
  ✅ OTP sent to +1xxxxxxxxxx
  OTP Code : xxxxxx
```

If **Two-Factor Authentication (2FA)** is enabled on the account:

```
  🔒 Two-Factor Authentication required.
  2FA Password : ••••••••••
```

Wrong password? It loops and lets you retry without restarting.

### 💾 Auto-Login on Future Runs

After the first login, credentials are saved to **`ashlynn_config.txt`**:

```
<api_id>
<api_hash>
<session_string>
```

Every subsequent run connects automatically — no login prompt needed.

> [!WARNING]
> **Keep `ashlynn_config.txt` private.** It contains your session string which grants full access to your Telegram account.  
> - Never share it or commit it to a public repository.
> - It is already listed in `.gitignore` for your protection.
> - To revoke access: go to **Telegram → Settings → Devices** and terminate the session.

---

## 📥 Fetching Media

Once connected, the tool enters an interactive loop:

```
  ════════════════════════════════════════════════════
  🔗 Link [folder] [replace="find"="with"]  |  q = quit
  >
```

### Input Format

```
<telegram_link> [optional_folder_name] [replace="find"="with"]
```

| Part | Required | Description |
|------|----------|-------------|
| `telegram_link` | ✅ Yes | Full `https://t.me/...` message URL |
| `optional_folder_name` | ❌ No | Sub-folder inside `AshlynnTGDL/` |
| `replace="find"="with"` | ❌ No | Rename rule applied to every fetched filename |

---

## 🔗 Supported Link Formats

| Type | Example |
|------|---------|
| Public channel / group | `https://t.me/channelname/1423` |
| Private channel (numeric ID) | `https://t.me/c/1234567890/10` |
| Message range (public) | `https://t.me/channelname/100-120` |
| Message range (private) | `https://t.me/c/1234567890/50-84` |
| Single message + folder | `https://t.me/channelname/42 movies` |
| Range + folder | `https://t.me/c/1234567890/49-84 lectures` |
| Range + folder + rename | `https://t.me/c/.../49-84 lectures replace="_BrandName"=""` |

> **Tip:** Right-click any message in Telegram → *Copy Message Link* to get the URL.

---

## 📁 Folder System

All files are saved inside the **`AshlynnTGDL/`** base folder, created automatically in the current directory.

### Without a folder name
```
Input  :  https://t.me/channel/100-120
Saves to: AshlynnTGDL/
```

### With a custom folder name
```
Input  :  https://t.me/channel/49-84 Accounting-Lectures
Saves to: AshlynnTGDL/Accounting-Lectures/
```

Folders are created automatically. Use hyphens or underscores instead of spaces in folder names.

---

## ✏️ Filename Renaming (replace=)

Strip or replace any unwanted text from **every filename** in a batch — useful when channels append their own branding text to file names.

### Syntax
```
replace="find_text"="replace_with"
```

| Goal | Syntax | Example result |
|------|--------|----------------|
| **Remove** a string | `replace="_BrandName"=""` | `Lecture_BrandName.mp4` → `Lecture.mp4` |
| **Replace** a string | `replace="_BrandName"="_Clean"` | `Lecture_BrandName.mp4` → `Lecture_Clean.mp4` |
| No renaming | *(omit replace= entirely)* | original filename kept |

### Example

```
https://t.me/c/1234567890/49-84 Lectures replace="_ABC_XYZ"=""
```

Before → After for every file in the batch:
```
Topic_Chapter01_ABC_XYZ.mp4
              ↓
Topic_Chapter01.mp4
```

> - File **extension is never modified** (`.mp4`, `.pdf`, etc. always preserved)
> - If the find text is absent from a filename, that file downloads with its original name
> - Supports Unicode and bold/stylized text characters

---

## 📊 Live Progress Bar

Every file fetch shows a real-time progress bar:

```
  🎬 [3/36]  LectureVideo.mp4  (Video, 350.70 MB)
  [██████████████████████████████████████]  100.0%  2.51 MB/s  350.70 MB / 350.70 MB  ETA: 0s
  ✅ Saved  →  LectureVideo.mp4
```

| Indicator | Meaning |
|-----------|---------|
| `[████████]` | Visual fill bar (updates live) |
| `100.0%` | Percentage complete |
| `2.51 MB/s` | Real-time transfer speed |
| `350.70 MB / 350.70 MB` | Transferred / Total size |
| `ETA: 0s` | Estimated time remaining |

> **⚡ Speed Note**  
> Transfer speed depends on several factors:
> - 🌐 **Your internet connection** — faster network = faster transfers
> - 📡 **Telegram's Data Centre** — your account's assigned DC affects throughput
> - 🔑 **Account type** — Telegram Premium accounts may receive higher bandwidth allocation
> - 🕐 **Server load** — Telegram servers may be busier at peak hours
> - 📦 **File size & type** — larger files may start slower then ramp up
>
> Under a good connection you can generally expect **2–5 MB/s**. `PyroTgCrypto` (native C extension) eliminates CPU as a bottleneck — your network is the only real limit.

---

## 🛡️ Account Safety

> [!IMPORTANT]
> Fetching large amounts of media in a short time **may trigger Telegram's automated rate limiting**, which can slow down or temporarily restrict your account's API access. AshlynnTGDL includes built-in protections:

| Protection | How it works |
|------------|-------------|
| **Inter-file delay** | 1.5s pause between every file fetch |
| **10-file cooldown** | Extra 6s pause after every 10 files |
| **50-file safety break** | Extra 20s pause after every 50 files |
| **FloodWait respect** | If Telegram signals a wait, the tool sleeps the exact required time |
| **Auto-retry with backoff** | Failed fetches retry up to 2 times with increasing wait (3s, 6s) |

> [!WARNING]
> Even with these protections, **you are responsible for your own account's safety.**
> - Avoid fetching thousands of files per day from a single account.
> - Do not use this tool on accounts that are already restricted or flagged
> - The author is **not responsible** for any account limitations, bans, or data loss resulting from misuse

---

## 📋 Fetch Summary

After each batch completes:

```
  ────────────────────────────────────────────────────
  📊 Done!  🎬 34 media  📝 1 text  ⚠️  1 skipped
  📁 Saved to : C:\Users\...\AshlynnTGDL\Accounting-Lectures
```

---

## 🛠️ Build a Standalone Executable

### Windows

```bat
build.bat
```
Produces: `AshlynnTGDL.exe`

### Linux / macOS

```bash
chmod +x build.sh
./build.sh
```
Produces: `AshlynnTGDL` binary

> `pyinstaller` is installed automatically by the build script.

---

## 📂 Project Structure

```
AshlynnTGDL/
├── ashlynntgdl.py       # Main entry point
├── utils.py             # Progress bar, helpers, banner, config path
├── requirements.txt     # kurigram + PyroTgCrypto
├── build.bat            # Windows build script
├── build.sh             # Linux/macOS build script
├── ashlynn_config.txt   # Auto-created after first login (keep private!)
└── AshlynnTGDL/         # Auto-created output folder
    ├── video.mp4
    ├── document.pdf
    └── my-folder/       # Custom sub-folders
        └── lecture.mp4
```

---

## ❓ FAQ

**Q: What chats/channels can I fetch from?**  
A: Only chats and channels where **your Telegram account is already a member**. This tool uses your own account's API access — it has the same permissions as the Telegram app on your phone.

**Q: Is my session string safe?**  
A: It is stored locally in `ashlynn_config.txt` and only ever sent to Telegram's official MTProto servers — the same servers your Telegram app connects to. Never share this file.

**Q: What if I get `FloodWait` errors?**  
A: AshlynnTGDL automatically detects Telegram's rate-limit signals and waits the exact required duration before continuing. No action needed.

**Q: I want to re-login or switch accounts.**  
A: Delete `ashlynn_config.txt` and re-run the script. You can also revoke the session from **Telegram → Settings → Devices**.

**Q: Can I fetch multiple batches in one session?**  
A: Yes! After each batch completes, it asks `Download more? (y/n)` — answer `y` to continue.

**Q: Will this get my account banned?**  
A: This tool uses the official Telegram MTProto API — the same protocol used by all Telegram clients. However, **excessive usage in a short period may trigger Telegram's automated systems.** The built-in delays significantly reduce this risk. Use responsibly.

---

## ⚙️ Supported Media Types

| Type | Icon |
|------|------|
| Video | 🎬 |
| Audio | 🎵 |
| Document | 📄 |
| Photo | 🖼️ |
| Sticker | 🎯 |
| Animation (GIF) | 🎞️ |
| Voice Message | 🎙️ |
| Video Note (round video) | 📹 |
| Text Message | 📝 |

---

## 📜 License

This project is licensed under the **MIT License** — free to use, modify, and distribute.

This project uses the **Telegram MTProto API** through the [Kurigram](https://pypi.org/project/kurigram/) client library. Telegram's API is a publicly available, documented interface. This tool does not exploit any vulnerability or undocumented behavior.

---

> [!NOTE]
> **This project is for educational and personal archival purposes only.**  
> It demonstrates client-session based media fetching using the official Telegram MTProto API.  
> Always respect content ownership, copyright, and Telegram's Terms of Service. 

---

<div align="center">

## 🌐 Links

[![GitHub](https://img.shields.io/badge/GitHub-Itz--Ashlynn%2FAshlynnTGDL-181717?style=for-the-badge&logo=github)](https://github.com/Itz-Ashlynn/AshlynnTGDL)
[![Telegram](https://img.shields.io/badge/Telegram-Ashlynn_Repository-2CA5E0?style=for-the-badge&logo=telegram)](https://t.me/Ashlynn_Repository)

---

*Made with ❤️ by **Aarabh** · [Ashlynn Repository](https://t.me/Ashlynn_Repository)*

</div>
