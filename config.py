import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    @property
    def TELEGRAM_BOT_TOKEN(self) -> str:
        load_dotenv()
        return os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    @property
    def GEMINI_API_KEY(self) -> str:
        load_dotenv()
        return os.getenv("GEMINI_API_KEY", "").strip()

    @property
    def NOTION_API_KEY(self) -> str:
        load_dotenv()
        return os.getenv("NOTION_API_KEY", "").strip()
        
    @property
    def ALLOWED_TELEGRAM_USER_IDS(self) -> List[int]:
        load_dotenv()
        raw = os.getenv("ALLOWED_TELEGRAM_USER_IDS", "").strip()
        if not raw:
            return []
        ids = []
        for uid in raw.split(","):
            clean = uid.strip()
            if clean and clean.isdigit():
                ids.append(int(clean))
        return ids

    @property
    def PORT(self) -> int:
        load_dotenv()
        return int(os.getenv("PORT", "8000"))

    @property
    def WEBHOOK_URL(self) -> str:
        load_dotenv()
        return os.getenv("WEBHOOK_URL", "").strip()

    @property
    def DAILY_BRIEFING_ENABLED(self) -> bool:
        load_dotenv()
        return os.getenv("DAILY_BRIEFING_ENABLED", "true").strip().lower() in ("true", "1", "yes")

    @property
    def DAILY_BRIEFING_TIME(self) -> str:
        load_dotenv()
        return os.getenv("DAILY_BRIEFING_TIME", "06:00").strip()

    @property
    def UTC_OFFSET_HOURS(self) -> float:
        load_dotenv()
        try:
            return float(os.getenv("UTC_OFFSET_HOURS", "8"))
        except ValueError:
            return 8.0

    @property
    def EMAIL_NOTIFICATIONS_ENABLED(self) -> bool:
        load_dotenv()
        raw = os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "").strip().lower()
        if raw in ("false", "0", "no"):
            return False
        # Enabled by default if recipient email and credentials exist, or explicitly set to true
        return raw in ("true", "1", "yes") or bool(self.NOTIFICATION_EMAIL_TO and (self.SMTP_USER or self.RESEND_API_KEY))

    @property
    def NOTIFICATION_EMAIL_TO(self) -> str:
        load_dotenv()
        return os.getenv("NOTIFICATION_EMAIL_TO", "").strip()

    @property
    def SMTP_HOST(self) -> str:
        load_dotenv()
        return os.getenv("SMTP_HOST", "smtp.gmail.com").strip()

    @property
    def SMTP_PORT(self) -> int:
        load_dotenv()
        try:
            return int(os.getenv("SMTP_PORT", "587"))
        except ValueError:
            return 587

    @property
    def SMTP_USER(self) -> str:
        load_dotenv()
        return os.getenv("SMTP_USER", "").strip()

    @property
    def SMTP_PASSWORD(self) -> str:
        load_dotenv()
        return os.getenv("SMTP_PASSWORD", "").strip()

    @property
    def EMAIL_FROM_NAME(self) -> str:
        load_dotenv()
        return os.getenv("EMAIL_FROM_NAME", "Andrei's Notion AI Assistant").strip()

    @property
    def EMAIL_FROM_ADDRESS(self) -> str:
        load_dotenv()
        from_addr = os.getenv("EMAIL_FROM_ADDRESS", "").strip()
        if from_addr:
            return from_addr
        return self.SMTP_USER or "briefing@notion-assistant.app"

    @property
    def RESEND_API_KEY(self) -> str:
        load_dotenv()
        return os.getenv("RESEND_API_KEY", "").strip()

    @property
    def ENABLE_TELEGRAM(self) -> bool:
        load_dotenv()
        raw = os.getenv("ENABLE_TELEGRAM", "").strip().lower()
        if raw in ("true", "1", "yes"):
            return True
        if raw in ("false", "0", "no"):
            return False
        # If not explicitly specified, only enabled if TELEGRAM_BOT_TOKEN is set
        return bool(os.getenv("TELEGRAM_BOT_TOKEN", "").strip())

    @property
    def WEB_SESSION_SECRET(self) -> str:
        load_dotenv()
        return os.getenv("WEB_SESSION_SECRET", "").strip()

    @property
    def WEB_PASSWORD_HASH(self) -> str:
        load_dotenv()
        return os.getenv("WEB_PASSWORD_HASH", "").strip()

    @property
    def WEB_ALLOWED_ORIGINS(self) -> List[str]:
        load_dotenv()
        raw = os.getenv("WEB_ALLOWED_ORIGINS", "").strip()
        defaults = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        if not raw:
            return defaults
        origins = [o.strip() for o in raw.split(",") if o.strip()]
        for d in defaults:
            if d not in origins:
                origins.append(d)
        return origins

    @property
    def WEB_SESSION_DAYS(self) -> int:
        load_dotenv()
        try:
            return int(os.getenv("WEB_SESSION_DAYS", "30"))
        except ValueError:
            return 30

    @property
    def DATABASE_PATH(self) -> str:
        load_dotenv()
        return os.getenv("DATABASE_PATH", "data/life_hub.db").strip()

    @property
    def UPLOAD_DIR(self) -> str:
        load_dotenv()
        return os.getenv("UPLOAD_DIR", "data/uploads").strip()

    @property
    def WEB_PUSH_VAPID_PUBLIC_KEY(self) -> str:
        load_dotenv()
        return os.getenv("WEB_PUSH_VAPID_PUBLIC_KEY", "").strip()

    @property
    def WEB_PUSH_VAPID_PRIVATE_KEY(self) -> str:
        load_dotenv()
        raw = os.getenv("WEB_PUSH_VAPID_PRIVATE_KEY", "").strip()
        # Handle single-line representation with \n
        if "\\n" in raw:
            return raw.replace("\\n", "\n")
        return raw

    @property
    def WEB_PUSH_CONTACT(self) -> str:
        load_dotenv()
        return os.getenv("WEB_PUSH_CONTACT", "mailto:andrei@example.com").strip()

    def is_authorized(self, user_id: int) -> bool:
        allowed = self.ALLOWED_TELEGRAM_USER_IDS
        if not allowed:
            # Strict Fail-Closed: deny all access if whitelist is not explicitly configured
            return False
        return user_id in allowed

settings = Settings()
