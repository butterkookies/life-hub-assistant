# 📘 Andrei's Life Hub Assistant — Onboarding & Architecture Guide

> **For AI Assistants & Developers:** This document is the source of truth for understanding, running, maintaining, and extending **Andrei’s Life Hub Assistant** — an installable mobile-first PWA and FastAPI backend that connects Andrei directly to his Notion workspace and calendar. Telegram is maintained as an optional secondary fallback. The Electron desktop widget is maintained separately in the sibling `NOTION-WIDGET` directory.

---

## Notion routing update (2026-09-05)

Life Hub Manager is now a workspace-level page (`3be27102528781969765dedd1b639a0b`).
The old Life Hub is retained separately for reference; its Tasks/Projects databases are legacy destinations.

- Canonical Tasks database: `d1527102528783299cac81b9d565b99b`; data source: `96927102528782d9bed487a7322ac310`.
- Canonical Projects database: `ba427102528782efbdce815b505396a2`; data source: `59827102528783dbb9e807b71c738058`.
- `create_task` writes master Tasks rows with optional `Do Date` and `Projects` relation. The current Tasks schema has no Priority column.
- `create_project` creates a master Projects entry and a filtered linked Tasks view inside it. Every project shares the master task source; separate databases are reserved for specialized data or explicit requests.
- `ensure_project_tasks_view` repairs partial view setup without recreating the project. Repeating a project name reuses an existing active exact match; duplicate matches require explicit selection.
- `get_workspace_context` and `get_database_schema` expose canonical IDs and live schemas. Generic database creation validates requested fields and uses a data-source parent; failed writes never retry with fields removed.
- The Notion SDK must be `>=3.1.0,<4` for linked view creation. See the [Notion views API](https://developers.notion.com/guides/data-apis/working-with-views).
- Older architecture descriptions below may still use "Life Hub" as the app name. Do not infer a Notion write destination from that name.

Verification covers routing, legacy destination rejection, property preservation, pagination, and partial project recovery in `tests/test_notion_workspace.py`. A live check also verified creation, readback, view reuse, and cleanup of temporary project/task records.

Remaining recommendations: durable operation IDs to prevent duplicate writes across model retries; persisted tool-result receipts alongside chat history; migration of legacy checklists only after reviewing their intended projects and dates. These are not implemented by the routing update.

### Push notifications on the hosted app

The user-facing deployment is `https://life-hub-assistant.onrender.com`. Local server settings do not configure Render.
Set `WEB_PUSH_VAPID_PUBLIC_KEY`, `WEB_PUSH_VAPID_PRIVATE_KEY`, and `WEB_PUSH_CONTACT` in the Render service environment. Keep the matching key pair stable across deployments; never commit private keys. The private key may be PEM (including escaped newlines) or base64 DER/raw. The server parses PEM before calling pywebpush and uses separate claims for each device's push provider.

Each device must subscribe through Settings > Daily Briefing & Web Push. Windows users should open the hosted app in Chrome or Edge; iPhone users must add the HTTPS app to their Home Screen and open that installed app before granting notification permission. Device status is checked against the current browser subscription, rather than another device's registration. Send Test Notification sends to all registered devices; zero accepted sends is reported as failure. Provider acceptance does not prove display on the device.

Production subscriptions and conversation state live in Neon PostgreSQL, while uploads use private Cloudflare R2 storage. A Cloudflare Worker wakes the free Render service at 05:58 Asia/Manila and calls the idempotent briefing endpoint at 06:00. The installed PWA serves its cached shell immediately while the backend wakes.

---

## 📑 Table of Contents

1. [Executive Summary & Core Value](#1-executive-summary--core-value)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Repository File Map & Responsibilities](#3-repository-file-map--responsibilities)
4. [Notion Workspace & Database Schemas](#4-notion-workspace--database-schemas)
5. [Web PWA & Shared Backend Architecture](#5-web-pwa--shared-backend-architecture)
   - [FastAPI & Security Layer](#fastapi--security-layer)
   - [Agent Registry & Transport-Neutral Assistant](#agent-registry--transport-neutral-assistant)
   - [PostgreSQL/SQLite Persistence & Idempotency](#postgresqlsqlite-persistence--idempotency)
   - [Workout Confirmation Pipeline](#workout-confirmation-pipeline)
   - [Web Push & Briefing Scheduler](#web-push--briefing-scheduler)
6. [Configuration & Environment Variables](#6-configuration--environment-variables)
7. [Getting Started & Local Execution](#7-getting-started--local-execution)
8. [Testing & Diagnostics Suite](#8-testing--diagnostics-suite)
9. [Tailscale Serve HTTPS & iPhone PWA Setup](#9-tailscale-serve-https--iphone-pwa-setup)
10. [Developer Extension Guide (How to Add Features)](#10-developer-extension-guide-how-to-add-features)

---

## 1. Executive Summary & Core Value

This project is a personal AI productivity assistant built specifically for **Andrei** to interact with his Notion **"Life Hub"** workspace and Notion Calendar.

**Primary Interface**: An installable, mobile-first Progressive Web App (PWA) optimized for iPhone, iPad, and Windows, featuring in-app voice notes via `MediaRecorder`, treadmill display workout scanning with interactive confirmations, morning briefings, and Web Push notifications.

**Optional Fallback**: Telegram bot (`ENABLE_TELEGRAM=false` by default).

**Key Design Principle: $0 Infrastructure Cost**
Runs entirely on free tiers:
- Local Windows hosting exposed securely via Tailscale Serve (Free Private HTTPS)
- Google Gemini 2.5 / 3.x Flash via Google AI Studio API (Free Tier)
- Notion API v1 (Free Internal Integration)
- Web Push via browser VAPID (Free)
- Email via Resend REST API (Free Tier) or standard Gmail/Outlook SMTP

---

## 2. End-to-End System Architecture

```
[ 📱 iPhone / iPad (Safari PWA) ] ────── [ 💻 Windows / Desktop Browser ]
              │                                      │
              │  (Touch, In-App Voice, Camera)       │  (Desktop Web, Mic)
              ▼                                      ▼
     [ 🔒 Tailscale Serve (Free End-to-End HTTPS: https://<node>.ts.net) ]
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │    FASTAPI BACKEND (server/)    │
                    │  - PBKDF2/HMAC Session Auth     │
                    │  - Security Headers & CSRF      │
                    │  - In-App Voice & Workout Scans │
                    │  - VAPID Web Push Notifications │
                    │  - Daily Briefing Scheduler     │
                    └───────┬─────────────────┬───────┘
                            │                 │
              ┌─────────────▼───┐       ┌─────▼──────────┐
              │ SQLite Database │       │ Agent Registry │
              │ data/life_hub.db│       │ ('notion' ...) │
              └─────────────────┘       └─────┬──────────┘
                                              │
                      ┌───────────────────────▼──────┐
                      │    TRANSPORT-NEUTRAL CORE    │
                      │  (assistant_service.py)      │
                      └───────┬───────────────┬──────┘
                              │               │
      ┌───────────────────────▼─────┐   ┌─────▼────────────────────────┐
      │   GOOGLE GEMINI 2.5/3 FLASH │   │      notion_service.py       │
      │   - 6-Tier Resilient Chain  │   │  - Tasks, Calendar, Projects │
      │   - Dynamic Tool Execution  │   │  - Notes, Thought Inbox      │
      │   - Treadmill OCR & Valid.  │   │  - Daily Health & Workout    │
      └─────────────────────────────┘   └──────────────┬───────────────┘
                                                       │ (HTTPS API)
                                                       ▼
[ 📱 Telegram Bot (Optional) ] ───► [ NOTION CLOUD WORKSPACE ("Life Hub") ]
(telegram_bot.py, secondary fallback)
```

---

## 3. Repository File Map & Responsibilities

```
NOTION/
├── config.py                      # Centralized configuration with dynamic .env reload & auth checking
├── gemini_agent.py                # Gemini AI engine, 6-tier fallback, multimodal audio, Notion function tools
├── notion_service.py              # Python service layer wrapping official notion-client SDK & schema mapping
├── email_service.py               # HTML email templating engine and SMTP / Resend API dispatcher
├── telegram_bot.py                # Decoupled Telegram bot daemon (optional secondary interface)
├── generate_password_hash.py      # CLI tool for generating PBKDF2-HMAC-SHA256 password hashes
├── generate_vapid_keys.py         # CLI tool for generating Web Push VAPID key pairs
├── backup_database.py             # Live SQLite online backup snapshot utility (backups/)
├── restore_database.py            # SQLite database restore utility from snapshot
├── run_dev.bat                    # 1-click Windows launcher for Vite dev server + Uvicorn reload
├── run_prod.bat                   # 1-click Windows launcher for production build + Uvicorn server
├── requirements.txt               # Backend Python dependencies (FastAPI, Uvicorn, pywebpush, pytest, etc.)
│
├── server/                        # FastAPI Backend & Core Services
│   ├── main.py                    # FastAPI application, security middleware, SPA static mount & lifespan
│   ├── database.py                # PostgreSQL/SQLite connection adapter and schema management
│   ├── storage.py                 # Private R2/local object storage adapter
│   ├── models.py                  # Strongly-typed internal persistence dataclasses
│   ├── schemas.py                 # Pydantic request & response API contracts
│   ├── auth.py                    # PBKDF2 password hashing, HMAC-signed session cookies, rate limiting
│   ├── dependencies.py            # FastAPI dependencies for auth, user resolution, CSRF validation
│   ├── routes/                    # API Route Handlers
│   │   ├── auth.py                # /api/auth/login, /api/auth/logout, /api/auth/session
│   │   ├── agents.py              # /api/agents (Agent discovery & capability enumeration)
│   │   ├── conversations.py       # /api/conversations (CRUD, history list, delete)
│   │   ├── messages.py            # /api/conversations/{id}/messages (Send text, assistant dispatch)
│   │   ├── media.py               # /api/conversations/{id}/attachments, image scan confirmation
│   │   ├── notifications.py       # /api/notifications (Web Push subscribe, test, briefing trigger)
│   │   └── health.py              # /api/health (System status, Notion & Gemini health check)
│   └── services/                  # Business Logic Services
│       ├── agent_registry.py      # Transport-neutral agent registry (default: 'notion' Life Hub)
│       ├── assistant_service.py   # Core turn orchestrator with rolling SQLite conversation history
│       ├── conversation_service.py# Conversation CRUD, message persistence, user scoping
│       ├── workout_scan_service.py# Image validation, Gemini workout analysis, pending review cards
│       ├── briefing_service.py    # Manila-time daily morning briefing generator & dispatcher
│       └── web_push_service.py    # VAPID Web Push notifications dispatcher & stale sub cleanup
│
├── web/                           # Mobile-First Progressive Web App (PWA)
│   ├── index.html                 # Viewport cover, iOS standalone meta tags, theme color
│   ├── package.json               # React 18, TypeScript, Tailwind CSS, Lucide icons, Vite
│   ├── vite.config.ts             # Vite configuration with proxy to FastAPI backend
│   ├── tailwind.config.js         # Notion color palette, hairline borders, safe-area utilities
│   ├── public/
│   │   ├── manifest.webmanifest   # PWA manifest with standalone display and app metadata
│   │   ├── sw.ts                  # Injected service worker: precache, navigation fallback, push notifications
│   │   └── icons/                 # PWA icons (icon-192, icon-512, icon-maskable-512, apple-touch-icon)
│   └── src/
│       ├── types/index.ts         # TypeScript interfaces & API contracts
│       ├── lib/api.ts             # Typed fetch API client with credentials & CSRF handling
│       ├── lib/sanitize.ts        # Markdown rendering with marked + DOMPurify sanitization
│       ├── hooks/                 # Custom React hooks (useAuth, useConversations, useMediaRecorder)
│       ├── components/            # React UI Components (Header, ConversationDrawer, Timeline,
│       │                          #   MessageComposer, MessageItem, PendingScanCard, LoginModal,
│       │                          #   IosInstallGuide, PushNotificationModal)
│       ├── App.tsx                # Main application component & layout state
│       └── main.tsx               # Entry point & Service Worker registration
│
├── tests/                         # Automated Unit & E2E Test Suite (65+ tests)
│   ├── test_server_auth.py        # PBKDF2 hashing, rate limits, cookie sessions
│   ├── test_server_conversations.py # Conversation isolation, message ordering, duplicate prevention
│   ├── test_server_assistant.py   # Assistant dispatch, tool calling, error sanitization
│   ├── test_server_media.py       # Magic bytes validation, voice notes, attachment serving
│   ├── test_server_workout_scan.py# Scan review cards, token confirm/edit/cancel
│   ├── test_server_notifications_and_briefings.py # Web push subscriptions & morning briefing
│   ├── test_server_e2e_mobile.py  # End-to-end simulated mobile workflow
│   ├── test_gemini_image.py       # Gemini workout extraction
│   ├── test_image_models.py       # Pydantic workout validation schemas
│   ├── test_notion_workout.py     # Notion Daily Health database upserts
│   └── test_telegram_images.py    # Telegram image handler unit tests
│
├── Dockerfile                     # Docker container configuration running FastAPI on port 8000
├── Procfile                       # Process definition for web hosting (web: uvicorn server.main:app)
├── render.yaml                    # Cloud deployment specification
├── README.md                      # Public-facing documentation & quickstart
└── ONBOARDING.md                  # Detailed developer & AI architecture guide (THIS FILE)
```

---

## 4. Notion Workspace & Database Schemas

The workspace is organized around Andrei's **Life Hub**. Notion API changes in 2025/2026 introduced `data_source` objects alongside traditional `database` objects. The backend seamlessly handles both database IDs and data source IDs.

### Known Data Sources & IDs

| Database / Entity | UUID / Data Source ID | Description |
| :--- | :--- | :--- |
| **Tasks Database** | `d1527102528783299cac81b9d565b99b`<br>*(DS: `96927102528782d9bed487a7322ac310`)* | Main actionable tasks and calendar items. |
| **Projects Database** | `ba427102528782efbdce815b505396a2`<br>*(DS: `59827102528783dbb9e807b71c738058`)* | Top-level projects (e.g. BSIT-31A, Cianotes App, Personal). |
| **Workstreams** | `51127102528782ed8a80816bc58e66a1`<br>*(DS: `97227102528782ad81b707fb6d42c4d5`)* | High-level academic / professional workstreams. |
| **Notes** | `2f37a332d3d2412eb52130f52c279318`<br>*(DS: `d4e6043c84e045d2a63b45ad038819f7`)* | Workspace notes and documentation. |
| **Thought Inbox** | `ea7c1cc69135485fbe4d0f7fd4947a00`<br>*(DS: `6e61a09d80e94e5ba56d0f94772cc1f1`)* | Quick scratchpad and brain-dump entries. |
| **Daily Health & Workout Log** | `3c327102528781669c3cc7d7acfaa2a4`<br>*(DS: `3c327102528781ab8777000b115b3f54`)* | One daily row for health data and validated TRAX treadmill statistics. |

### Tasks Database Schema & Property Types

- **`Name`** (*title*): The task title (e.g., "Complete 3D FaceModel activity").
- **`Do Date`** / **`Date`** / **`Due Date`** (*date*): Target execution date in `YYYY-MM-DD` format.
- **`Status`** (*status* or *select*): `Not started` | `In progress` | `Done`.
- **`Priority`** (*select*): `Low` | `Normal` | `High Priority`.
- **`Projects`** (*relation*): One-to-many relation referencing the Projects database.
- **`Archive`** (*checkbox*): Boolean flag. Archived tasks are excluded from active widget & bot views.

### Dynamic Property Normalization

In `notion_service.py`, `_normalize_key()` and `_format_property_val()` automatically map flexible shorthand names sent by Gemini (e.g., `"due": "2026-08-29"`, `"project": "<id>"`, `"status": "done"`) into strictly formatted Notion API payload structures (`date`, `relation`, `status`, `select`, `checkbox`, `rich_text`).

---

## 5. Web PWA & Shared Backend Architecture

### FastAPI & Security Layer

Located in [`server/`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/server/), the backend is built on **FastAPI** with a fail-closed single-user security model:

1. **PBKDF2-HMAC-SHA256 Password Authentication**:
   - Password hashes use 600,000 iterations of PBKDF2 with a cryptographically secure 16-byte random salt (`server/auth.py`). Compatible with Argon2 fallback.
   - Verified in constant time via `hmac.compare_digest`.
2. **Brute-Force & Credential Stuffing Protection**:
   - In-memory sliding-window rate limiter tracks failed login attempts by client IP.
   - Exceeding 5 failed attempts locks the IP out for 15 minutes.
3. **Cryptographically Signed Session Cookies**:
   - Sessions are signed with HMAC-SHA256 using `WEB_SESSION_SECRET`.
   - Set as `HttpOnly`, `SameSite=Lax`, and `Secure` (in HTTPS production).
   - Valid for 30 days (`WEB_SESSION_DAYS`).
4. **Strict CSRF & Origin Verification**:
   - `server/dependencies.py` enforces Origin and Referer header checks on all state-changing HTTP verbs (`POST`, `PUT`, `PATCH`, `DELETE`) against `WEB_ALLOWED_ORIGINS`.
5. **Security Headers Middleware**:
   - `Content-Security-Policy`: Disallows untrusted external script execution.
   - `X-Frame-Options: DENY`: Prevents clickjacking.
   - `X-Content-Type-Options: nosniff`: Mitigates MIME-sniffing exploits.
   - `Referrer-Policy: strict-origin-when-cross-origin`.
   - `Permissions-Policy: microphone=(self), camera=(self), geolocation=()`.
6. **Upload Magic-Byte Verification**:
   - `server/routes/media.py` enforces both file size caps (<= 15 MiB) and binary file signature checks (JPEG `FF D8 FF`, PNG `89 50 4E 47`, WebP `RIFF...WEBP`, HEIC/HEIF `ftypheic`, audio `webm`, `mp4`, `ogg`).

---

### Agent Registry & Transport-Neutral Assistant

Located in [`server/services/assistant_service.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/server/services/assistant_service.py) and [`server/services/agent_registry.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/server/services/agent_registry.py):

- **Transport Neutrality**: AI logic is completely decoupled from whether the user connects via PWA, API, or optional Telegram.
- **Agent Registry**:
  - Initializes with the default `'notion'` agent: **Life Hub Assistant**.
  - Provides a clean interface (`IAgent`) allowing Andrei or future developers to plug in specialized agents (e.g. Code Agent, Finance Agent, Fitness Agent) without modifying routing or persistence code.
- **Multi-Tier Gemini Fallback Chain**:
  - Automatically handles free-tier rate limits and model hiccups by cascading through 6 prioritized tiers:
    1. `gemini-3.5-flash-lite` (Fastest, low latency)
    2. `gemini-3.1-flash-lite` (Stable high efficiency)
    3. `gemini-flash-lite-latest` (Production lite release)
    4. `gemini-3-flash-preview` (Full reasoning speed)
    5. `gemini-3.7-flash` (Multimodal)
    6. `gemini-2.5-flash` (Rock-solid fallback)
- **Autonomous Notion Tool Calling**:
  - Native tools include: `get_calendar_schedule`, `search_notion`, `get_page_content`, `query_database`, `create_database_item`, `update_page_properties`, `append_to_page`, `create_new_page`, and `create_database` (supports custom properties and view layouts: table, list, board, gallery, calendar, timeline).
- **Rolling Context Window**:
  - Rehydrates conversation turns directly from the SQLite `messages` table, pruning to the latest 20 turns with token-budget protection.

---

### PostgreSQL/SQLite Persistence & Idempotency

Located in [`server/database.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/server/database.py) and [`server/services/conversation_service.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/server/services/conversation_service.py):

- Production database: Neon PostgreSQL through `DATABASE_URL`.
- Local database: `data/life_hub.db` (automatically created, gitignored).
- **Local SQLite Engine Configuration**:
  - WAL mode (`PRAGMA journal_mode=WAL`) enabled for high-concurrency read/write operations.
  - Foreign key constraints enabled (`PRAGMA foreign_keys=ON`).
  - Busy timeout set to 5000ms to prevent lock contention.
- **Tables**:
  - `users`: Single-user credentials and role.
  - `sessions`: Active session tokens, expiry, client IP, and user-agent metadata.
  - `conversations`: Conversation threads scoped by agent (`agent_id`) and user.
  - `messages`: Message turns (`role`, `content`, `tool_calls`, `client_message_id`).
  - `attachments`: In-app voice notes and camera photos with file metadata and MIME types.
  - `pending_image_scans`: Pending workout scans awaiting interactive confirmation.
  - `push_subscriptions`: Browser VAPID endpoints and authentication keys for Web Push.
  - `briefing_deliveries`: Delivery audit log preventing duplicate morning briefings per day.
  - `briefing_runs`: Date-level dispatch claim preventing duplicate generation across scheduler retries.
  - `object_cleanup_queue`: Failed R2 deletions retained for retry on the next process start.
  - `storage_objects`: Object sizes used to enforce the 5 GB hosted-storage ceiling.
  - `storage_usage_daily`: Daily R2 operation counts used for rolling 31-day limits.
- **Network Idempotency**:
  - PWA generates a unique `client_message_id` for every outgoing message.
  - If a mobile connection stutters and retries, the backend returns the existing message without re-invoking Gemini or creating duplicate Notion entries.
- **Local Snapshots & Hosted Import**:
  - `python backup_database.py`: Performs a non-blocking online SQLite backup to `backups/life_hub_YYYYMMDD_HHMMSS.db`.
  - `python restore_database.py <snapshot>`: Restores state with safety checks.
  - `python scripts/migrate_sqlite_to_durable.py`: Imports local records and attachment objects into Neon/R2.

---

### Workout Confirmation Pipeline

Located in [`server/services/workout_scan_service.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/server/services/workout_scan_service.py):

1. **Capture & Upload**: User takes or attaches a photo of the treadmill console from iPhone PWA or desktop.
2. **Sanitization & Extraction**: Magic bytes and file size are verified. Gemini extracts structured metrics into a Pydantic `ImageAnalysis` schema:
   - Date, duration, distance, steps, calories, speed, heart rate, program, confidence score.
3. **Range & Plausibility Validation**: Enforces sanity checks (e.g. speed <= 25 km/h, heart rate 40-220 bpm, calories <= 3000).
4. **Notion Conflict Detection**: Queries Notion's `Daily Health & Workout Log` for existing entries on the target date.
5. **Interactive Review Card**:
   - Generates a pending scan record with a secure 10-minute token.
   - PWA renders a rich review card with metric badges, confidence indicator, and conflict warnings.
   - Actions:
     - **Save to Notion**: Confirms and upserts the metrics into Notion's `Daily Health & Workout Log` and attaches the image.
     - **Edit Values**: Allows manual adjustment of speed, distance, or duration before committing.
     - **Cancel**: Discards the pending scan and cleans up the temporary upload.

---

### Web Push & Briefing Scheduler

Located in [`server/services/web_push_service.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/server/services/web_push_service.py) and [`server/services/briefing_service.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/server/services/briefing_service.py):

- **VAPID Web Push**:
  - Implements RFC 8291 / 8292 using `pywebpush`.
  - Fully compatible with iOS 16.4+ standalone PWAs added to Home Screen.
  - Generates notifications for morning briefings, workout confirmations, and reminders.
  - Automatically detects 404/410 GCM/APNs responses and purges expired subscriptions.
- **Automated Morning Briefing**:
  - Cloudflare Worker Cron wakes Render at 05:58 and calls `POST /api/internal/briefings/daily` at 06:00 AM (Asia/Manila time, UTC+8).
  - Fetches today's tasks and calendar events from Notion.
  - Gemini synthesizes an executive summary: priorities, schedule, health focus, and daily motivation.
  - Automatically records the briefing to the in-app timeline, sends a Web Push alert, and sends an HTML email newsletter if configured.

---

### Telegram Bot (Decoupled Secondary Fallback)

Located in [`telegram_bot.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/telegram_bot.py):

- Fully decoupled: defaults to `ENABLE_TELEGRAM=false`.
- If enabled with `ENABLE_TELEGRAM=true` and a valid token, runs as an optional secondary interface for quick mobile input.
- Shares the underlying `gemini_agent.py` and `notion_service.py` functions without conflicting with the web server.

---

## 6. Configuration & Environment Variables

Create or update `.env` in the repository root:

```env
# ==============================================================================
# WEB APP & SECURITY CONFIGURATION
# ==============================================================================
# PBKDF2 hash of your web login password (generate with: python generate_password_hash.py)
WEB_PASSWORD_HASH=pbkdf2:sha256:600000$salt$hash

# Random secret string for HMAC session cookie signing (at least 32 characters)
WEB_SESSION_SECRET=generate_a_long_random_secret_string_here_32chars

# Allowed CORS & CSRF origins (comma-separated). Include your Tailscale Serve domain.
WEB_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8000,http://127.0.0.1:8000,https://andrei-pc.tailscale.net

# Session cookie lifetime in days (default: 30)
WEB_SESSION_DAYS=30

# Local SQLite path and hosted PostgreSQL URL
DATABASE_PATH=data/life_hub.db
DATABASE_URL=postgresql://...

# Local upload path and hosted private R2 configuration
UPLOAD_DIR=uploads
R2_ENDPOINT_URL=https://ACCOUNT_ID.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret
R2_BUCKET=life-hub-uploads
R2_MAX_STORAGE_BYTES=5368709120
R2_MAX_WRITES_31D=100000
R2_MAX_READS_31D=1000000
DURABLE_STORAGE_REQUIRED=true
BRIEFING_TRIGGER_TOKEN=generate_a_long_random_scheduler_secret

# ==============================================================================
# WEB PUSH NOTIFICATIONS (VAPID)
# ==============================================================================
# Generate with: python generate_vapid_keys.py
WEB_PUSH_VAPID_PUBLIC_KEY=your_vapid_public_key_base64
WEB_PUSH_VAPID_PRIVATE_KEY=your_vapid_private_key_base64
WEB_PUSH_CONTACT=mailto:andrei@example.com

# ==============================================================================
# AI ENGINE CONFIGURATION (GOOGLE GEMINI)
# ==============================================================================
# API key from Google AI Studio (https://aistudio.google.com)
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere

# ==============================================================================
# NOTION WORKSPACE INTEGRATION
# ==============================================================================
# Internal Integration Secret from https://www.notion.so/my-integrations
NOTION_API_KEY=ntn_your_notion_api_key_here

# ==============================================================================
# MORNING BRIEFING & SCHEDULE SETTINGS
# ==============================================================================
# Enable/disable automated 6:00 AM daily briefing (true/false)
DAILY_BRIEFING_ENABLED=false
DAILY_BRIEFING_TIME=06:00
UTC_OFFSET_HOURS=8

# ==============================================================================
# EMAIL NOTIFICATIONS (OPTIONAL)
# ==============================================================================
EMAIL_NOTIFICATIONS_ENABLED=false
NOTIFICATION_EMAIL_TO=andrei@example.com
RESEND_API_KEY=re_your_resend_api_key_here

# ==============================================================================
# TELEGRAM BOT (OPTIONAL SECONDARY FALLBACK)
# ==============================================================================
ENABLE_TELEGRAM=false
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ALLOWED_TELEGRAM_USER_IDS=1234567890

# ==============================================================================
# SERVER PORT
# ==============================================================================
PORT=8000
```

---

## 7. Getting Started & Local Execution

### Prerequisites
- **Python 3.12+** or **Python 3.14+**
- **Node.js 20+** and **npm**
- Active Notion integration added to your Notion `Life Hub` workspace page.

---

### Step 1: Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Build the Frontend PWA
```bash
cd web
npm install
npm run build
cd ..
```

### Step 3: Generate Security Credentials
```bash
# 1. Generate password hash for your access password:
python generate_password_hash.py -p your_secure_password_here

# 2. Generate VAPID keys for Web Push:
python generate_vapid_keys.py
```
Copy the outputs into your `.env` file.

### Step 4: Validate Connections
```bash
python test_connections.py
```

### Step 5: Launch the Application
- **Production Mode (Recommended)**:
  Double-click `run_prod.bat` or run:
  ```bash
  python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
  ```
  The production server serves both the FastAPI API and the compiled React PWA from `web/dist`.
- **Development Mode**:
  Double-click `run_dev.bat` to launch Vite on port 5173 with hot-reloading and FastAPI on port 8000 with auto-reload.

---

## 8. Testing & Diagnostics Suite

The repository includes a comprehensive automated test suite covering all critical services, security mechanisms, and user flows:

```bash
# Run the complete test suite:
python -m pytest tests -v
```

### Test Coverage Summary

| Test File | Verified Functionality |
| :--- | :--- |
| `tests/test_server_auth.py` | PBKDF2 password hashing, rate limiting, session cookie signing, CSRF protection. |
| `tests/test_server_conversations.py` | Conversation creation, message sequencing, idempotent retry handling (`client_message_id`). |
| `tests/test_server_assistant.py` | Transport-neutral dispatch, tool calling, error sanitization, context window rolling. |
| `tests/test_server_media.py` | Magic bytes binary validation, audio voice notes, photo attachments, path traversal protection. |
| `tests/test_server_workout_scan.py` | Treadmill scan review flow, token confirmation, manual value edits, cancellation. |
| `tests/test_server_notifications_and_briefings.py` | VAPID push subscriptions, duplicate briefing prevention, manual briefing trigger. |
| `tests/test_server_e2e_mobile.py` | Full simulated iPhone session: login -> voice note -> workout scan -> save -> timeline check. |
| `tests/test_gemini_image.py` | Gemini treadmill OCR extraction accuracy. |
| `tests/test_image_models.py` | Pydantic schema validation for workout metrics. |
| `tests/test_notion_workout.py` | Notion `Daily Health & Workout Log` upsert logic. |
| `tests/test_telegram_images.py` | Telegram photo and callback query handlers. |

---

## 9. Tailscale Serve HTTPS & iPhone PWA Setup

Tailscale Serve provides a **100% free, end-to-end encrypted HTTPS URL** backed by a valid Let's Encrypt certificate directly on your Windows PC, enabling iOS Safari PWA installation without opening router ports or buying domains.

### Step 1: Install Tailscale on Windows & iPhone
1. Install [Tailscale for Windows](https://tailscale.com/download/windows) and sign in.
2. Install [Tailscale for iOS](https://apps.apple.com/app/tailscale/id1470499037) on your iPhone and sign in with the same account.
3. Verify MagicDNS is active in your Tailscale admin console.

### Step 2: Enable Tailscale Serve on Windows
Run this command in PowerShell as Administrator:
```powershell
tailscale serve --bg 8000
```
Tailscale outputs your private HTTPS URL, for example:
```
https://andrei-pc.tailscale.net
```

### Step 3: Configure Allowed Origins
Add your Tailscale URL to `.env`:
```env
WEB_ALLOWED_ORIGINS="http://localhost:8000,https://andrei-pc.tailscale.net"
```

### Step 4: Install on iPhone
1. Open **Safari** on your iPhone.
2. Navigate to `https://andrei-pc.tailscale.net`.
3. Log in with your password.
4. Tap the **Share** button in Safari's bottom toolbar.
5. Tap **"Add to Home Screen"** and confirm.
6. Launch **"Life Hub"** from your Home Screen. It opens in full-screen standalone mode with native iOS gestures, safe-area padding, and in-app voice/camera recording!

---

## 10. Developer Extension Guide (How to Add Features)

### A. Adding a New Agent to the Registry
1. Implement the `IAgent` protocol in `server/services/agent_registry.py`:
   ```python
   class MySpecializedAgent:
       id = "finance"
       name = "Finance Assistant"
       description = "Tracks expenses and budgets in Notion."
       system_instruction = "..."
       tools = [...]
   ```
2. Register the agent in `AgentRegistry`:
   ```python
   registry.register(MySpecializedAgent())
   ```
3. The PWA's agent dropdown in the header will automatically discover and display the new agent!

### B. Adding a New Tool to the Notion Assistant
1. Implement the Notion API call in [`notion_service.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/notion_service.py).
2. Define the tool function with detailed docstrings in [`gemini_agent.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/gemini_agent.py).
3. Add the function to `TOOLS` in `gemini_agent.py`. Gemini will autonomously invoke it when relevant.

### C. Adding a New Database to the Workspace
1. Locate the Notion database UUID from your Notion URL.
2. Add the UUID and its corresponding Data Source ID into `KNOWN_DATA_SOURCES` in [`notion_service.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/notion_service.py).
3. If property normalization is required, update `_normalize_key()` and `_format_property_val()`.

### 💡 Quick Tips for Future AI Agents
- **Notion 2025/2026 API Versioning**: When querying databases, the Notion API often requires querying the `data_source` endpoint rather than `databases/{id}/query`. `notion_service.py` includes automatic fallback logic. Maintain this pattern for all new database operations.
- **Windows SQLite Locks**: When running tests on Windows, open database handles can trigger `WinError 32` during directory cleanup. Always use `TemporaryDirectory(ignore_cleanup_errors=True)` and explicitly close test clients.
- **Frontend Code Quality**: The frontend is built with strict TypeScript (`noImplicitAny: true`). Always run `cd web && npx tsc --noEmit && npm run build` after modifying UI code.
