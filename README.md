# 🏛️ Andrei's Life Hub Assistant (Mobile-First PWA + FastAPI + Notion AI)

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.3-61DAFB.svg)](https://react.dev/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini%202.5%20Flash-orange.svg)](https://aistudio.google.com/)
[![Notion API](https://img.shields.io/badge/Notion-API%20v1-black.svg)](https://developers.notion.com/)
[![PWA](https://img.shields.io/badge/PWA-Installable-purple.svg)](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An installable, mobile-first Progressive Web App (PWA) named **"Andrei's Life Hub Assistant"** (short name: **"Life Hub"**) that connects Andrei directly to his **Notion Workspace (Life Hub)** and **Notion Calendar** using **Google Gemini AI**.

It replaces Telegram as the primary interaction medium while running on a **100% free, zero-cost personal deployment** on Windows exposed privately and securely to iPhone and iPad via **Tailscale Serve (HTTPS)**.

---

## 🌟 Highlights

- 📱 **Mobile-First Installable PWA**: Designed specifically for iPhone (Safari "Add to Home Screen" standalone mode), iPad, Windows, and modern desktop/mobile browsers. Full iOS safe-area support (`viewport-fit=cover`), touch targets, and offline app shell caching.
- 🎨 **Notion Design System**: Warm paper canvas (`#fbfbfa`), pure white cards (`#ffffff`), hairline borders (`#e9e9e8`), Inter typography, Notion blue accents (`#0075de`), and layered micro-shadows.
- 🎙️ **Native In-App Voice Notes**: Hold or tap the mic button to record voice notes directly in the browser/PWA via `MediaRecorder`. Gemini transcribes your speech and executes Notion workspace actions with zero external paid transcription APIs.
- 📷 **Treadmill Display Workout Scanner**: Take or attach a treadmill photo; Gemini extracts structured metrics (duration, distance, steps, calories, speed, heart rate) with plausibility checks, conflict detection against Notion, and interactive **Save / Edit / Cancel** review cards.
- 🌅 **Automated Morning Briefings**: Generates crisp, motivating morning briefings based on today's Notion schedule and tasks (Asia/Manila time, UTC+8), delivered to Web Push, email, or your in-app briefing timeline.
- 🔔 **Web Push Notifications**: Standards-based Web Push via VAPID (compatible with iOS 16.4+ standalone Home Screen apps).
- 🔒 **Ironclad Single-User Security**: Password authentication with PBKDF2-HMAC-SHA256 (600,000 rounds), signed HttpOnly Secure cookies, sliding-window rate limiting, CSRF origin verification, and upload magic-byte verification.
- 🗄️ **Local SQLite Persistence**: Conversations, messages, tool summaries, upload metadata, and pending workout scans persist in `data/life_hub.db` outside version control.
- ⚡ **$0 Hosting & Infrastructure**: Runs on your Windows computer exposed securely over Tailscale with Tailscale Serve providing free, valid HTTPS.

---

## 🏛️ System Architecture

```
[ 📱 iPhone / iPad (Safari PWA) ] ──── [ 💻 Windows / Desktop Browser ]
                       │                        │
                       ▼                        ▼
      [ 🔒 Tailscale Serve (Free Private HTTPS) ]
                       │
                       ▼
      [ 🚀 FastAPI Application (server/main.py) ]
         ├── Security Headers, CSRF & Cookie Session Auth
         ├── SQLite Persistence (data/life_hub.db)
         ├── Web Push Notification Dispatcher (VAPID)
         │
         ▼
      [ 🧠 Transport-Neutral Assistant Service ]
         │
         ├──▶ [ Google Gemini 2.5 / 3.5 Flash Engine ]
         │       └── Multi-Tier Free-Tier Fallback Chain
         │
         └──▶ [ 🔌 Notion Service API (notion_service.py) ]
                 └── Calendar, Tasks, Notes, Daily Health Log
```

---

## 🚀 Quickstart & Setup Guide

### 1. Prerequisites
- **Python 3.12+** or **Python 3.14+**
- **Node.js 20+** and **npm**
- Active Notion Integration connected to your Notion `Life Hub` workspace page (click `•••` -> **Connections** -> add your integration).

### 2. Install Dependencies
```bash
# Python backend dependencies
pip install -r requirements.txt

# Web frontend dependencies
cd web
npm install
npm run build
cd ..
```

### 3. Generate Security Credentials
Generate your password hash and VAPID keys using the included helper scripts:

```bash
# 1. Generate your access password hash:
python generate_password_hash.py -p your_secure_password_here

# 2. Generate your Web Push VAPID keys:
python generate_vapid_keys.py
```

### 4. Configure Your `.env` File
Create `.env` in the project root:
```env
# ==============================================================================
# Web App Authentication
# ==============================================================================
WEB_PASSWORD_HASH="pbkdf2:sha256:600000$your_salt$your_hash"
WEB_SESSION_SECRET="your_random_secret_session_key_at_least_32_characters_long"
WEB_ALLOWED_ORIGINS="http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"

# ==============================================================================
# AI & Notion Keys
# ==============================================================================
GEMINI_API_KEY=your_gemini_api_key_here
NOTION_API_KEY=ntn_your_notion_integration_secret_here

# ==============================================================================
# Web Push Notifications (Optional)
# ==============================================================================
WEB_PUSH_VAPID_PUBLIC_KEY="your_public_key"
WEB_PUSH_VAPID_PRIVATE_KEY="your_private_key"
WEB_PUSH_CONTACT="mailto:your_email@example.com"

# ==============================================================================
# Daily Briefings & Schedule (Asia/Manila is UTC+8)
# ==============================================================================
DAILY_BRIEFING_ENABLED=true
DAILY_BRIEFING_TIME=06:00
UTC_OFFSET_HOURS=8

# ==============================================================================
# Optional Telegram Fallback (Disabled by default)
# ==============================================================================
ENABLE_TELEGRAM=false
PORT=8000
```

---

## 🏃 Running the Application

### Option A: 1-Click Production Mode (Recommended)
Double-click `run_prod.bat` in the project root, or execute:
```bash
run_prod.bat
```
The server will compile the frontend (if needed) and run on `http://127.0.0.1:8000`.

### Option B: 1-Click Live-Reload Development Mode
Double-click `run_dev.bat` in the project root, or execute:
```bash
run_dev.bat
```
Starts FastAPI on `http://127.0.0.1:8000` and Vite with hot module replacement on `http://localhost:5173`.

---

## 📱 iPhone & iPad Setup via Tailscale Serve (100% Free HTTPS)

Tailscale provides private encrypted networking and automatically signs free, trusted TLS certificates for your machines:

1. Install [Tailscale](https://tailscale.com) on your Windows PC and iPhone.
2. Sign in to both devices under the same Tailscale account.
3. Enable HTTPS on your Windows PC by running in PowerShell (as Administrator):
   ```powershell
   tailscale serve --bg 8000
   ```
4. Tailscale gives you a private HTTPS URL, for example:
   `https://my-windows-pc.your-tailnet.ts.net`
5. Open that URL in **Safari** on your iPhone.
6. Tap the **Share** button in Safari (box with upward arrow) ➔ scroll down and tap **Add to Home Screen** ➔ tap **Add**.
7. Open **Life Hub** from your Home Screen! It runs as a native standalone app with full offline shell caching, camera access, voice recording, and push notifications.

---

## 💾 Database Backups & Restore

The SQLite database is stored locally in `data/life_hub.db`. Use the automated tools to create crash-safe point-in-time snapshots:

```bash
# Create a live online backup:
python backup_database.py
# Output saved to: backups/life_hub_backup_YYYYMMDD_HHMMSS.db

# Restore from the most recent backup:
python restore_database.py

# Or restore from a specific file:
python restore_database.py -f backups/life_hub_backup_20260904_102632.db
```

---

## 🧪 Testing & Verification Suite

Run the full automated test suite (65+ tests) verifying auth, sessions, CSRF, idempotency, media uploads, workout confirmations, briefing scheduler, and mobile flows:

```bash
python -m pytest tests
```

To typecheck and test the frontend:
```bash
cd web
npx tsc --noEmit
npm run build
```

---

## 🧩 Extending with New AI Agents

The application features a transport-neutral agent architecture. To add a new specialized agent:
1. Open [`server/services/agent_registry.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/server/services/agent_registry.py).
2. Register your agent definition with `id`, `name`, `description`, and `capabilities`.
3. Route incoming messages in [`server/services/assistant_service.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/server/services/assistant_service.py) based on `agent_id`.
4. The agent will automatically appear in the Life Hub header dropdown on both mobile and desktop!
