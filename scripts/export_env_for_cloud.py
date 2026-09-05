"""Helper script to safely export environment variables from .env for Render/Railway/Cloud hosting."""

import os
import sys
from pathlib import Path
from dotenv import dotenv_values

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def main():
    env_file = Path(".env")
    if not env_file.exists():
        print("[!] No .env file found in current directory.")
        return

    values = dotenv_values(env_file)
    
    # Priority keys needed for cloud deployment
    cloud_keys = [
        "WEB_PASSWORD_HASH",
        "WEB_SESSION_SECRET",
        "GEMINI_API_KEY",
        "NOTION_API_KEY",
        "DAILY_BRIEFING_ENABLED",
        "DAILY_BRIEFING_TIME",
        "UTC_OFFSET_HOURS",
        "EMAIL_NOTIFICATIONS_ENABLED",
        "NOTIFICATION_EMAIL_TO",
        "EMAIL_FROM_NAME",
        "EMAIL_FROM_ADDRESS",
        "SMTP_HOST",
        "SMTP_PORT",
        "SMTP_USER",
        "SMTP_PASSWORD",
        "RESEND_API_KEY",
        "WEB_SESSION_DAYS",
        "WEB_PUSH_VAPID_PUBLIC_KEY",
        "WEB_PUSH_VAPID_PRIVATE_KEY",
        "WEB_PUSH_CONTACT",
    ]

    print("=" * 60)
    print("COPIABLE ENVIRONMENT VARIABLES FOR CLOUD HOSTING")
    print("(Render > Environment > Bulk Edit, or Railway Raw Editor)")
    print("=" * 60)

    for k in cloud_keys:
        val = values.get(k)
        if val is not None and val.strip() != "":
            print(f"{k}={val.strip()}")

    print("=" * 60)
    print("Tip for Render (https://dashboard.render.com):")
    print(" 1. Click New + -> Web Service -> Connect butterkookies/life-hub-assistant")
    print(" 2. Environment: Docker (auto-detected via Dockerfile)")
    print(" 3. Under Environment Variables, click 'Add from .env' or paste lines above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
