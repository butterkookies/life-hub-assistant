# Hosting Andrei's Life Hub Assistant

This guide explains how to host **Andrei's Life Hub Assistant** so you can install and use it as an iOS PWA on your iPhone anywhere in the world (5G, Wi-Fi) over secure HTTPS without needing Tailscale or VPN profiles.

---

## Option 1: Render (Recommended — 100% Free 24/7 Cloud)

Render automatically builds both your React frontend and FastAPI backend from your GitHub repository using the multi-stage `Dockerfile`.

### Step 1: Create a Web Service on Render
1. Go to [dashboard.render.com](https://dashboard.render.com) and log in with your GitHub account.
2. Click **New +** in the top right, then select **Web Service**.
3. Under *Connect a repository*, choose **`butterkookies/life-hub-assistant`**.

### Step 2: Configure Service Settings
- **Name**: `life-hub-assistant` (or your preferred name)
- **Region**: Singapore (`Southeast Asia`) or Oregon (`US West`) — *Singapore gives lower latency from the Philippines*
- **Branch**: `main`
- **Runtime**: **Docker** *(auto-detected via `Dockerfile`)*
- **Instance Type**: **Free** ($0.00/mo)

### Step 3: Add Environment Variables
Render provides an **"Add from .env"** or bulk edit option:
1. In your local terminal on your PC, run:
   ```bash
   python scripts/export_env_for_cloud.py
   ```
2. Copy the output block of `KEY=VALUE` pairs.
3. In Render under **Environment Variables**, click **"Add from .env"** (or Add Environment Variable) and paste them in.
4. Essential variables:
   - `GEMINI_API_KEY`: Google Gemini API key
   - `NOTION_API_KEY`: Notion Integration token
   - `WEB_PASSWORD_HASH`: Your PBKDF2 password hash
   - `WEB_SESSION_SECRET`: Your session secret
   - `DAILY_BRIEFING_TIME`: `06:00`
   - `UTC_OFFSET_HOURS`: `8`
   - `EMAIL_NOTIFICATIONS_ENABLED`: `true` (if email configured)
   - `NOTIFICATION_EMAIL_TO`: Your email address

### Step 4: Deploy & Access
1. Click **Deploy Web Service**.
2. Render will build the Docker container (compiling the TypeScript frontend + configuring FastAPI backend).
3. Once the log says `Application startup complete`, Render will provide your permanent public HTTPS URL:
   `https://life-hub-assistant.onrender.com`
4. On your iPhone:
   - Open Safari and navigate to `https://life-hub-assistant.onrender.com`.
   - Log in with your password.
   - Tap Safari **Share** icon -> **Add to Home Screen**.
   - Enjoy your standalone full-screen Life Hub app!

---

## Option 2: Railway (Best Performance & Persistent Volume)

Railway gives instant response times and optional persistent storage for SQLite chat logs.

1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. Click **New Project** -> **Deploy from GitHub repo** -> Select `butterkookies/life-hub-assistant`.
3. Go to **Variables** tab -> Click **Raw Editor** -> Paste the output of `python scripts/export_env_for_cloud.py`.
4. Go to **Settings** tab -> Under **Networking**, click **Generate Domain**.
5. Railway provides your custom domain: `https://<service>.up.railway.app`.

---

## Option 3: Cloudflare Quick Tunnel (Host from your PC, Zero Cloud Signup)

If you prefer keeping everything running locally on your computer with instantaneous speed and persistent local SQLite storage:

1. Download `cloudflared` (or run `winget install --id Cloudflare.cloudflared`).
2. Start the local server:
   ```cmd
   run_prod.bat
   ```
3. In a separate terminal, run:
   ```cmd
   cloudflared tunnel --url http://127.0.0.1:8000
   ```
4. Cloudflare will output a public HTTPS address like:
   `https://random-words.trycloudflare.com`
5. Open that URL on your iPhone Safari and add to Home Screen!
