# 📘 Notion AI Assistant & Desktop Widget — Onboarding & Architecture Guide

> **For ChatGPT / AI Assistants & Developers:** This document serves as the single source of truth for understanding, running, maintaining, and extending this codebase. It covers the full ecosystem: the **Telegram AI Bot** (with Google Gemini 2.5/3.x function calling and voice notes), the **Proactive Morning Briefing & Email Dispatcher**, and the **Windows Desktop Home Screen Widget** (React 19 + Electron + Notion Design System).

---

## 📑 Table of Contents

1. [Executive Summary & Core Value](#1-executive-summary--core-value)
2. [End-to-End System Architecture](#2-end-to-end-system-architecture)
3. [Repository File Map & Responsibilities](#3-repository-file-map--responsibilities)
4. [Notion Workspace & Database Schemas](#4-notion-workspace--database-schemas)
5. [Telegram Bot & AI Engine](#5-telegram-bot--ai-engine)
   - [Gemini Agent & Multi-Tier Fallback](#gemini-agent--multi-tier-fallback)
   - [Autonomous Function Calling / Tool Registry](#autonomous-function-calling--tool-registry)
   - [Multimodal Voice-to-Action Pipeline](#multimodal-voice-to-action-pipeline)
   - [Image-to-Notion Workout Pipeline](#image-to-notion-workout-pipeline)
   - [Automated Morning Briefing Scheduler](#automated-morning-briefing-scheduler)
   - [Email Service (HTML Newsletters & Alerts)](#email-service-html-newsletters--alerts)
   - [Telegram HTML Formatting Engine](#telegram-html-formatting-engine)
   - [Security & Whitelisting Protocol](#security--whitelisting-protocol)
6. [Windows Desktop Home Screen Widget](#6-windows-desktop-home-screen-widget)
   - [Tech Stack & Design Philosophy](#tech-stack--design-philosophy)
   - [IPC Communication Contract](#ipc-communication-contract)
   - [Key Interactive Features](#key-interactive-features)
   - [Window Management & System Tray](#window-management--system-tray)
7. [Configuration & Environment Variables](#7-configuration--environment-variables)
8. [Getting Started & Local Execution](#8-getting-started--local-execution)
9. [Testing & Diagnostics Suite](#9-testing--diagnostics-suite)
10. [Developer Extension Guide (How to Add Features)](#10-developer-extension-guide-how-to-add-features)

---

## 1. Executive Summary & Core Value

This project is a personal AI productivity operating system built specifically for **Andrei** to interact seamlessly with his Notion **"Life Hub"** workspace and Notion Calendar across two primary modalities:

1. **Mobile / Everywhere (Telegram Bot)**:
   - Chat with a personalized AI assistant on Telegram via text or **native voice notes**.
   - Gemini autonomously queries and modifies Notion databases, retrieves schedules, appends to daily journals, and tracks workouts.
   - Automatically generates and sends a motivating, structured **Daily Morning Briefing** at 6:00 AM via Telegram and responsive HTML email.
2. **Desktop (Windows Home Screen Widget)**:
   - A modern desktop widget adhering to the **Notion DESIGN.md** design language (warm paper canvas `#f6f5f4`, clean white cards, hairline borders, project sticker pills, Inter typography).
   - Floats or pins to the desktop, provides instant optimistic check-offs, expandable note previews, quick inline task entry, search/filtering, and system tray minimization.

**Key Design Principle: $0 Infrastructure Cost**
Runs entirely on free tiers:
- Telegram Bot API (Free)
- Google Gemini 2.5 / 3.x Flash via Google AI Studio API (Free Tier)
- Notion API v1 (Free Internal Integration)
- Email via Resend REST API (Free Tier: 3,000 emails/month) or standard Gmail/Outlook SMTP
- Hosting: Render / Railway / Koyeb Free Background Workers or locally on Windows PC

---

## 2. End-to-End System Architecture

```
                                  ┌────────────────────────────────────────────────────────┐
                                  │                  ANDREI'S USER FLOW                    │
                                  └────────────────────────────────────────────────────────┘
                                               │                               │
                      [ 📱 Mobile Phone (Telegram) ]           [ 💻 Windows PC Desktop ]
                                   │                                           │
                   (Text Messages / Voice Audio Notes)               (Interactive GUI Widget)
                                   │                                           │
                                   ▼                                           ▼
                    ┌──────────────────────────────┐            ┌──────────────────────────────┐
                    │     telegram_bot.py          │            │  widget/electron/main.ts     │
                    │  - User Whitelist Auth       │            │  - Frameless Glass Window    │
                    │  - HTML Formatting Engine    │            │  - Tray & Global Shortcuts   │
                    │  - Daily 6:00 AM Scheduler   │            │  - JSON Config Store         │
                    └──────────────┬───────────────┘            └──────────────┬───────────────┘
                                   │                                           │
                    ┌──────────────▼───────────────┐            ┌──────────────▼───────────────┐
                    │     gemini_agent.py          │            │  widget/src/App.tsx (React)  │
                    │  - Google GenAI SDK (v1.0+)  │            │  - Optimistic State Updates  │
                    │  - 6-Tier Model Fallback     │            │  - Project Sticker Filters   │
                    │  - Voice Audio Decoder       │            │  - Task Preview Drawer       │
                    └──────────────┬───────────────┘            └──────────────┬───────────────┘
                                   │ (Function Calling)                        │ (Direct Node Client)
                                   │                                           │
                    ┌──────────────▼───────────────┐            ┌──────────────▼───────────────┐
                    │     notion_service.py        │            │ widget/electron/             │
                    │  - Query Databases           │            │   notion-client.ts           │
                    │  - Manage Calendar & Tasks   │            │  - Tasks & Projects Sync     │
                    │  - Page Content & Append     │            │  - Status & Preview Handler  │
                    └──────────────┬───────────────┘            └──────────────┬───────────────┘
                                   │                                           │
                                   └─────────────────────┬─────────────────────┘
                                                         │ (HTTPS Notion API)
                                                         ▼
                                       ┌───────────────────────────────────┐
                                       │     NOTION CLOUD WORKSPACE        │
                                       │  - Tasks Database                 │
                                       │  - Projects Database              │
                                       │  - Workstreams & Notes            │
                                       │  - Calendar Schedule              │
                                       └───────────────────────────────────┘

                    ┌──────────────────────────────┐
                    │     email_service.py         │ ───► [ 📧 Andrei's Email Inbox ]
                    │  - Responsive Newsletter HTML│      (Daily Morning Briefings & Alerts)
                    │  - Resend REST API / SMTP    │
                    └──────────────────────────────┘
```

---

## 3. Repository File Map & Responsibilities

```
NOTION/
├── config.py                      # Centralized configuration with dynamic .env reload & auth checking
├── telegram_bot.py                # Main Telegram bot daemon, commands, voice handler, scheduler, health server
├── gemini_agent.py                # Gemini AI agent, 6-tier fallback, multimodal audio, Notion function tools
├── notion_service.py              # Python service layer wrapping official notion-client SDK & schema mapping
├── email_service.py               # HTML email templating engine and SMTP / Resend API dispatcher
├── test_connections.py            # Diagnostic script validating Notion, Gemini, and Email connectivity
├── test_bot.py                    # Interactive test runner for quick terminal prompts
├── start_widget.bat               # Windows batch launcher (installs, builds, and launches Desktop Widget)
├── requirements.txt               # Python package dependencies
├── Procfile                       # Deployment process definition (worker: python telegram_bot.py)
├── Dockerfile                     # Docker container configuration for cloud hosting
├── render.yaml                    # Infrastructure-as-code for 1-click Render cloud deployment
├── README.md                      # Public-facing quickstart and features overview
├── ONBOARDING.md                  # Detailed developer & AI architecture guide (THIS FILE)
│
└── widget/                        # Modern Windows Desktop Widget (React 19 + Electron + TypeScript)
    ├── package.json               # Node.js dependencies (@notionhq/client, react 19, electron, tailwind)
    ├── tsconfig.json              # TypeScript compiler configuration
    ├── vite.config.ts             # Vite build & Electron bundling configuration
    ├── tailwind.config.js         # Notion Design System color palette, typography & shadows
    ├── index.html                 # HTML shell for Electron renderer
    ├── icon.png                   # System tray and application window icon
    ├── start.bat                  # Local launcher from within widget folder
    │
    ├── electron/                  # Electron Main Process (Node / Native Layer)
    │   ├── main.ts                # Window creation, bounds persistence, tray menu, global shortcut, IPC
    │   ├── preload.ts             # Secure contextBridge exposing window.electronAPI to React
    │   ├── preload.cjs            # CommonJS build output for preload
    │   ├── notion-client.ts       # Direct Notion SDK integration for fast desktop syncing
    │   └── types.ts               # Shared TypeScript interfaces for IPC & Notion data structures
    │
    ├── src/                       # React 19 Frontend (Renderer Layer)
    │   ├── main.tsx               # React DOM root mounting
    │   ├── App.tsx                # Main widget application state, filter/search logic, keyboard hooks
    │   ├── index.css              # Tailwind base, Notion font imports, scrollbar styling
    │   ├── lib/
    │   │   ├── types.ts           # Frontend TypeScript types (NotionTask, NotionProject, WidgetConfig)
    │   │   └── notion-theme.ts    # Notion project sticker palettes (color mapping, tags, borders)
    │   └── components/
    │       ├── Header.tsx         # Draggable header, sync indicator, pin toggle, settings/minimize triggers
    │       ├── DailyProgress.tsx  # Visual completion bar ("4 of 8 Completed · 50%")
    │       ├── FilterBar.tsx      # Today/Active/All tabs, search input, project sticker pill selector
    │       ├── TaskItem.tsx       # Individual task row with interactive status check, project pill, expand button
    │       ├── TaskPreviewDrawer.tsx # Expandable drawer rendering child blocks and markdown content
    │       ├── InlineTaskAdd.tsx  # Quick "+ New task..." input row at list bottom
    │       ├── QuickAddModal.tsx  # Full modal dialog for task creation with project & due date picker
    │       └── SettingsModal.tsx  # Widget preferences (opacity, always on top, auto-refresh interval)
    │
    └── legacy_python_widget/      # Archived CustomTkinter/Python desktop widget (superseded by Electron)
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

## 5. Telegram Bot & AI Engine

### Gemini Agent & Multi-Tier Fallback

Located in [`gemini_agent.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/gemini_agent.py), the `GeminiNotionAgent` class uses the modern `google-genai` Python SDK (`from google import genai`).

#### Multi-Tier Resilience Architecture
To prevent downtime from free-tier rate limits or transient model hiccups, queries attempt execution through a prioritized cascade:

1. **Gemini 3.5 Flash Lite** (`gemini-3.5-flash-lite`) — Ultra-fast, minimal latency.
2. **Gemini 3.1 Flash Lite** (`gemini-3.1-flash-lite`) — Stable high-efficiency tier.
3. **Gemini Flash Lite Latest** (`gemini-flash-lite-latest`) — Latest production lite release.
4. **Gemini 3 Flash** (`gemini-3-flash-preview`) — Full Gemini 3 reasoning speed.
5. **Gemini 3.7 Flash** (`gemini-3.7-flash`) — Cutting-edge multimodal model.
6. **Gemini 2.5 Flash** (`gemini-2.5-flash`) — Battle-tested reliable fallback.

If a fallback model is used, the response discreetly appends `_⚡ Handled via <Model Name> fallback_`.

#### Conversation History
Maintains rolling history per `user_id` up to 20 turns. If a corrupt state or bad request occurs, history is automatically reset for self-healing.

---

### Autonomous Function Calling / Tool Registry

The agent provides Gemini with native Python tools:

```python
TOOLS = [
    get_calendar_schedule,  # Fetches scheduled items for target date (YYYY-MM-DD)
    search_notion,          # Workspace-wide search for pages & databases
    get_page_content,       # Reads child blocks formatted as Markdown
    query_database,         # Queries items with filtering
    create_database_item,   # Creates a row with title, properties, & body
    update_page_properties, # Updates status (Done, In Progress), priority, date
    append_to_page,         # Appends bullet, todo, or paragraph blocks
    create_new_page         # Creates standalone child pages
]
```

Gemini autonomously decides when to query the calendar, search for project pages, create tasks, or read notes.

---

### Multimodal Voice-to-Action Pipeline

1. Andrei sends a voice message or audio clip on Telegram.
2. `telegram_bot.py` downloads the audio buffer as an in-memory byte stream (`audio/ogg`).
3. Audio bytes are passed directly into Gemini via `types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg")` with live date/time context.
4. Gemini transcribes the speech, extracts intent (e.g. "Add a reminder for Friday to back up files"), executes the appropriate Notion tool, and confirms the action.

---

### Image-to-Notion Workout Pipeline

1. An authorized user sends a Telegram photo or image document. Authentication is checked before any file download.
2. `telegram_bot.py` accepts JPEG, PNG, WebP, HEIC, and HEIF files up to 15 MiB, downloads the highest-resolution image into memory, and passes its bytes and caption to Gemini.
3. `gemini_agent.py` treats visible image text as untrusted data and returns a Pydantic-validated `ImageAnalysis`. Treadmill fields include date, duration, distance, steps, calories, speed, heart rate, program, workout type, confidence, and uncertainty markers.
4. Deterministic validators enforce plausible numeric ranges. Complete scans at 90% confidence or higher are eligible for automatic saving; uncertain scans display Telegram **Save**, **Edit**, and **Cancel** controls that expire after 10 minutes.
5. `notion_service.py` upserts one `Daily Health & Workout Log` row per date. Missing treadmill values are filled automatically, while conflicting existing values require explicit confirmation and unrelated health fields are never modified.
6. After a create or update, the original source image is uploaded to Notion and appended to the daily page. Metric writes remain saved if the attachment fails. Exact database matches are treated as duplicates and receive no additional image block.
7. Non-treadmill images are described but cannot write to Notion. The router is intentionally extensible for future receipt, task-list, calendar, and note handlers.

Image bytes remain in memory only and are discarded after completion, cancellation, or expiry. The bot retains Telegram file identifiers in process memory for 24 hours to suppress immediate reprocessing; no audit properties are added to the Notion data source.

---

### Automated Morning Briefing Scheduler

- In `telegram_bot.py`, an async background task `daily_briefing_scheduler()` runs indefinitely.
- Targets `DAILY_BRIEFING_TIME` (default `06:00` AM, `UTC_OFFSET_HOURS=8.0` for Asia/Manila).
- Workflow:
  1. Queries today's Notion tasks & schedule.
  2. Gemini synthesizes a structured executive summary:
     - ☀️ **Morning Greeting & Date**
     - 📋 **Today's Priorities & Schedule** (crisp breakdown of tasks/deadlines)
     - 🏃 **Health & Fitness Prompt** (treadmill walk, health check-in)
     - ⚡ **Daily Motivation** (short philosophical quote or focus reminder)
  3. Sends formatted Telegram HTML message to all `ALLOWED_TELEGRAM_USER_IDS`.
  4. If email is configured, sends a responsive HTML email newsletter to `NOTIFICATION_EMAIL_TO`.

---

### Email Service (HTML Newsletters & Alerts)

Located in [`email_service.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/email_service.py):
- **Template**: Styled with dark header gradients, clean white content cards, left accent borders (Blue for priorities, Green for health, Amber for motivation), and a direct button linking to Notion Life Hub.
- **Transports**:
  - **Resend REST API**: Uses `RESEND_API_KEY` (primary high-speed delivery).
  - **SMTP**: Fallback to standard SMTP (`smtp.gmail.com:587` with STARTTLS).

---

### Telegram HTML Formatting Engine

Telegram's Markdown parser is notoriously fragile with unescaped underscores and special characters. `telegram_bot.py` includes a custom parser (`format_for_telegram`):
1. Safely protects `<pre>` and `<code>` blocks using unique placeholder tags.
2. Escapes HTML entities (`<`, `>`, `&`).
3. Formats bullet points (`* ` / `- ` -> `• `).
4. Converts headers (`#`, `##`, `###`) into bold headers (`<b>...</b>`).
5. Translates markdown links `[text](url)` to `<a href="url">text</a>`.
6. Translates `**bold**`, `_italics_`, and horizontal dividers (`───────────────`).
7. Restores clean code blocks with proper syntax highlighting.

---

### Security & Whitelisting Protocol

- **Fail-Closed Auth**: `config.py` evaluates `settings.is_authorized(user_id)`. If `ALLOWED_TELEGRAM_USER_IDS` is empty or the user ID does not match, all requests receive immediate **403 Access Denied**.
- **Anti-Leak System Prompt**: Instructions explicitly forbid revealing API keys, tokens, or system configuration to anyone, even if prompted with jailbreaks.
- **Embedded Health Check Server**: An HTTP server runs on `PORT` (8000) answering `GET /` with `{"status":"healthy"}` to satisfy cloud hosting health probes (Render, Railway, Koyeb).

---

## 6. Windows Desktop Home Screen Widget

The widget in `widget/` is a native desktop application built with **React 19, TypeScript, Electron 34, and Tailwind CSS**.

### Tech Stack & Design Philosophy

- **Notion Design System (DESIGN.md)**:
  - Canvas: `#f6f5f4` (warm paper)
  - Card Surface: `#ffffff` with hairline border `#e6e6e6`
  - Notion Blue: `#0075de`
  - Subtle micro-shadows (`0 1px 2px rgba(0,0,0,0.04)`)
  - Project Sticker Pills (`#d3e5ef` blue, `#dbeddb` green, `#fdecc8` yellow, `#f1e0ec` pink, `#eedbf3` purple)
  - Tight-tracked typography (`Inter`, system fonts)

---

### IPC Communication Contract

The Electron main process (`widget/electron/main.ts`) and React frontend communicate via `window.electronAPI` exposed through `widget/electron/preload.ts`:

```typescript
export interface IElectronAPI {
  // Configuration
  getConfig: () => Promise<WidgetConfig>;
  saveConfig: (updates: Partial<WidgetConfig>) => Promise<WidgetConfig>;
  
  // Window & System Controls
  minimize: () => void;
  close: () => void;
  setAlwaysOnTop: (isTop: boolean) => void;
  openExternalUrl: (url: string) => void;
  
  // Notion Data Actions
  getProjects: () => Promise<NotionProject[]>;
  getTasks: (targetDate?: string) => Promise<NotionTask[]>;
  updateTaskStatus: (taskId: string, newStatus: string) => Promise<boolean>;
  createTask: (title: string, projectId?: string, priority?: string, doDate?: string) => Promise<NotionTask>;
  getPagePreview: (pageId: string) => Promise<PagePreviewData>;
  
  // Event Listeners (Push from Main to Renderer)
  onTriggerRefresh: (callback: () => void) => () => void;
  onTriggerQuickAdd: (callback: () => void) => () => void;
  onConfigUpdated: (callback: (cfg: Partial<WidgetConfig>) => void) => () => void;
}
```

---

### Key Interactive Features

1. **Optimistic Check-Offs**: Clicking the status circle toggles `Not started` -> `Done` instantly in the React state while syncing to Notion in the background. If sync fails, the state automatically reverts with an error banner.
2. **Page Preview Drawer**: Clicking any task expands an accordion drawer that reads child blocks (paragraphs, headers, todo checkboxes) directly from Notion without opening a browser.
3. **Daily Progress Metric**: Displays a progress bar with dynamic counts (e.g. `5 of 10 Completed · 50%`).
4. **Smart Filtering**:
   - Filter Tabs: `Today` (today's scheduled tasks), `Active` (all pending tasks), `All`.
   - Project Sticker Chips: Filter tasks by specific project with 1 click.
   - Instant Search: Real-time substring filter on task names and projects.
5. **Creation Methods**:
   - **Inline Quick Add**: Fast input bar at the bottom (`+ New task...` + Enter).
   - **Detailed Modal**: `+` button in the header opens full project selector and date picker.
6. **Global Shortcut & System Tray**:
   - `Ctrl+Shift+T` toggles widget visibility globally across Windows.
   - Minimizing or closing docks the widget cleanly to the Windows System Tray.
   - Right-click tray menu: "Show Tasks", "Refresh Tasks", "Add Task for Today", "Always on Top", "Launch on Windows Startup", "Exit".

---

## 7. Configuration & Environment Variables

Environment variables are defined in `.env` in the root folder. Both the Python services and the Electron widget auto-load this file.

```env
# ==============================================================================
# TELEGRAM BOT CONFIGURATION
# ==============================================================================
# Token from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Whitelist of allowed Telegram User IDs (from @userinfobot). Comma-separated for multiple.
ALLOWED_TELEGRAM_USER_IDS=1234567890

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
DAILY_BRIEFING_ENABLED=true

# Scheduled briefing time in 24-hour HH:MM format
DAILY_BRIEFING_TIME=06:00

# Local timezone offset from UTC (Default: 8 for Asia/Manila)
UTC_OFFSET_HOURS=8

# ==============================================================================
# EMAIL NOTIFICATIONS & MORNING NEWSLETTER (OPTIONAL)
# ==============================================================================
# Enable/disable email notifications (true/false)
EMAIL_NOTIFICATIONS_ENABLED=true

# Recipient email address
NOTIFICATION_EMAIL_TO=andrei@example.com

# Method 1: Resend API (Recommended - fast & modern)
RESEND_API_KEY=re_your_resend_api_key_here

# Method 2: Standard SMTP (Gmail / Outlook / SendGrid)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password_here
EMAIL_FROM_NAME=Andrei's Notion AI Assistant
EMAIL_FROM_ADDRESS=briefing@notion-assistant.app

# ==============================================================================
# CLOUD HOSTING & PORT BINDING
# ==============================================================================
PORT=8000
```

---

## 8. Getting Started & Local Execution

### Prerequisites
- **Python 3.12+** or **Python 3.14+**
- **Node.js 20+** and **npm**
- Active Notion integration connected to your Notion pages (Click `•••` -> **Connections** -> Select your Integration in Notion).

---

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Validate API Connections
Run the diagnostic suite to confirm Notion, Gemini, and Email credentials work:
```bash
python test_connections.py
```

### Step 3: Run the Telegram Bot
```bash
python telegram_bot.py
```

### Step 4: Run the Windows Desktop Widget

**Option A: 1-Click Batch File (Recommended)**
Double-click `start_widget.bat` in the project root. It will install packages, build the bundle, and open the widget.

**Option B: Manual Terminal Execution**
```bash
cd widget
npm install
npm run build
npm run start
```

**Option C: Vite Live-Reload Dev Mode**
```bash
cd widget
npm run dev
```

---

## 9. Testing & Diagnostics Suite

| Test Command | Purpose |
| :--- | :--- |
| `python test_connections.py` | Tests Notion API connection, Gemini model response, and email readiness. |
| `python test_bot.py` | Runs a dry-run prompt through the Gemini Agent without Telegram. |
| `python -m unittest discover -s tests -v` | Runs image validation, Gemini fallback, Notion upsert, attachment, authorization, and Telegram workflow unit tests. |
| `python -c "import config; print(config.settings.ALLOWED_TELEGRAM_USER_IDS)"` | Checks parsed Telegram user ID whitelist. |

### Telegram In-App Commands
- `/start` — Introduction & quick-action summary.
- `/help` — Example prompts for schedule, fitness tracking, and notes.
- `/status` — Verifies live Notion connection, accessible pages count, and active Gemini tiers.
- `/briefing` or `/briefing now` — Generates today's morning briefing immediately.
- `/briefing email` — Dispatches today's briefing to your email inbox.
- `/email status` — Inspects email provider (Resend vs SMTP) and recipient settings.
- `/email test` — Sends an immediate test email to verify delivery.
- Send a treadmill photo — Extracts workout statistics, auto-saves validated records, or presents Save/Edit/Cancel when review is needed.

---

## 10. Developer Extension Guide (How to Add Features)

### A. Adding a New Tool to the Gemini Agent
1. Open [`notion_service.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/notion_service.py) and add the Notion client logic.
2. Open [`gemini_agent.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/gemini_agent.py):
   - Define a tool function with clear docstrings explaining argument formats.
   - Add the function name to the `TOOLS` list.
3. Restart `telegram_bot.py`. Gemini will automatically begin calling the new tool when relevant.

### B. Adding a New Database to the Assistant
1. Find the Notion database ID (from the Notion URL).
2. Add the ID and its corresponding data source ID into `KNOWN_DATA_SOURCES` in [`notion_service.py`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/notion_service.py) and [`widget/electron/notion-client.ts`](file:///c:/Users/user/Documents/ANDREI_FILES/NOTION/widget/electron/notion-client.ts).
3. If specific property normalizations are required, update `_normalize_key()` and `_format_property_val()`.

### C. Modifying the Desktop Widget UI
1. All React components reside in `widget/src/components/`.
2. Design tokens (colors, radii, shadows) are defined in `widget/tailwind.config.js` and `widget/src/lib/notion-theme.ts`.
3. To expose new native OS features or Notion queries to the widget:
   - Add the IPC handler in `widget/electron/main.ts`.
   - Expose the method in `widget/electron/preload.ts`.
   - Declare the TypeScript signature in `widget/src/lib/types.ts`.
   - Call `window.electronAPI.yourMethod()` in React.
4. Run `npm run build` in `widget/` to compile changes.

---

## 💡 Quick Tips for Future AI Agents

- **Modifying System Prompt**: The system prompt for Gemini is in `gemini_agent.py` under `SYSTEM_INSTRUCTION`. Keep Telegram formatting rules and confidentiality guardrails intact.
- **Handling Free Tier Rate Limits**: The 6-tier fallback mechanism in `_execute_turn()` ensures high reliability. If adding models, add them to `MODEL_TIERS`.
- **Notion 2025/2026 API Versioning**: When querying databases, the Notion API sometimes requires queries to hit the `data_source` endpoint instead of `databases/{id}/query`. Both `notion_service.py` and `notion-client.ts` include automatic data-source resolution fallbacks. Keep this pattern for all new database operations.
