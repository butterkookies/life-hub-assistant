# 🤖 Notion AI Assistant (Telegram + Google Gemini + Notion API)

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini%202.5%20Flash-orange.svg)](https://aistudio.google.com/)
[![Notion API](https://img.shields.io/badge/Notion-API%20v1-black.svg)](https://developers.notion.com/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot%20API-2CA5E0.svg)](https://core.telegram.org/bots)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A personal, mobile-first AI assistant bot on **Telegram** that connects directly to your **Notion Workspace** and **Notion Calendar** using **Google Gemini 2.5 Flash**. 

Send text or record **voice notes** directly from your phone to manage tasks, query databases, append journal entries, and search documents with zero monthly subscription fees ($0).

---

## 🌟 Highlights

- 🎙️ **Native Voice-to-Action**: Send Telegram voice notes from your phone lock screen; Gemini automatically transcribes your speech, extracts the intent, and creates/queries entries in Notion.
- 🧠 **Autonomous Function Calling**: Gemini intelligently selects tools to search workspace pages, read full markdown docs, query database filters, or create tasks.
- 🔒 **Ironclad Privacy & Whitelisting**: Restricted exclusively to your authorized Telegram User ID (`ALLOWED_TELEGRAM_USER_IDS`). Any unauthorized sender receives an immediate 403 access denial.
- 🛡️ **Anti-Leak Guardrails**: AI system instructions prevent leaking internal environment variables, tokens, or system configurations.
- ⚡ **$0 Infrastructure**: Runs completely on free tiers (Telegram Bot API + Google AI Studio Free Tier + Notion API).

---

## 🏛️ System Architecture

```
[ 📱 Your Phone (Telegram App) ]
         │  (Text Message / Voice Audio Note)
         ▼
[ ☁️ Telegram Cloud API ]
         │  (Secure Long-Polling / Webhook)
         ▼
[ 💻 Python Bot Daemon (telegram_bot.py) ]
         │
         ├──▶ [ 🔒 User ID Whitelist Auth (config.py) ]
         │
         ├──▶ [ 🧠 Google Gemini 2.5 Flash Engine (gemini_agent.py) ]
         │           │
         │           ▼ (Function Calling)
         │      [ 🛠️ Tool Registry (search, read, create, append) ]
         │           │
         └──▶ [ 🔌 Notion Service API (notion_service.py) ]
                     │
                     ▼
          [ 🗄️ Notion Cloud Workspace & Databases ]
```

---

## 🚀 Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/butterkookies/notion-ai-bot.git
cd notion-ai-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Your Environment
Create your `.env` file from the template:
```bash
cp .env.example .env
```

Populate your `.env` with your credentials:
```env
# Telegram Bot Token (from @BotFather on Telegram)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Your Telegram User ID (from @userinfobot on Telegram)
ALLOWED_TELEGRAM_USER_IDS=1234567890

# Google Gemini API Key (from https://aistudio.google.com)
GEMINI_API_KEY=your_gemini_api_key_here

# Notion Internal Integration Secret (from https://www.notion.so/my-integrations)
NOTION_API_KEY=ntn_your_notion_integration_secret_here
```

> **Important**: In Notion, open your root workspace page (e.g. `Life Hub`), click `•••` in the top right ➔ **Connections** ➔ add your integration so the bot has read/write permission.

### 4. Run the Bot
```bash
python telegram_bot.py
```

---

## ☁️ 24/7 Cloud Deployment (100% Free)

To keep your bot running 24/7 without needing your personal computer turned on:

1. Push your repository to **GitHub** (keep it **Private**).
2. Create a free account at [Render](https://render.com) or [Railway](https://railway.app).
3. Create a new **Background Worker** service and connect your GitHub repo.
4. Add the 4 environment variables from your `.env` into the host dashboard.
5. Set the Start Command to:
   ```bash
   python telegram_bot.py
   ```
6. Click **Deploy**! Your bot is now active 24/7.

---

## 💬 Example Commands & Voice Prompts

| Interaction | Example Prompt | Action Performed |
| :--- | :--- | :--- |
| **Search Workspace** | *"What active projects do I have in my workspace?"* | Searches Notion databases and returns formatted summary links. |
| **Create Task** | *"Add high-priority task for BSIT-31A: 3D modeling due Friday"* | Adds a new row in the Tasks database linked to the project. |
| **Voice Note** | 🎙️ *(Speak: "Add a reminder to back up my Blender files this weekend")* | Transcribes audio, detects intent, and creates the reminder. |
| **Read Notes** | *"Read the page BSIT-31A and tell me what tasks are pending"* | Reads block content and outputs pending assignments. |
| **Quick Journal** | *"Add bullet point to my Daily Journal: Completed bot setup today"* | Appends a bullet block to your Journal page. |

---

## 🔒 Security & Privacy

- **Never Commits Secrets**: `.env` is ignored by default in `.gitignore`.
- **Sender Validation**: The bot validates every incoming message's `effective_user.id` against `ALLOWED_TELEGRAM_USER_IDS` before executing any LLM or Notion code.
- **Confidentiality Guardrails**: Gemini system instructions strictly forbid repeating or revealing environment tokens or internal IDs.

---

## 📄 License
Distributed under the MIT License. See `LICENSE` for more information.
