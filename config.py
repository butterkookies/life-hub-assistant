import os
from typing import List
from dotenv import load_dotenv

load_dotenv()

class Settings:
    @property
    def TELEGRAM_BOT_TOKEN(self) -> str:
        load_dotenv(override=True)
        return os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    @property
    def GEMINI_API_KEY(self) -> str:
        load_dotenv(override=True)
        return os.getenv("GEMINI_API_KEY", "").strip()

    @property
    def NOTION_API_KEY(self) -> str:
        load_dotenv(override=True)
        return os.getenv("NOTION_API_KEY", "").strip()
        
    @property
    def ALLOWED_TELEGRAM_USER_IDS(self) -> List[int]:
        load_dotenv(override=True)
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
        load_dotenv(override=True)
        return int(os.getenv("PORT", "8000"))

    @property
    def WEBHOOK_URL(self) -> str:
        load_dotenv(override=True)
        return os.getenv("WEBHOOK_URL", "").strip()

    def is_authorized(self, user_id: int) -> bool:
        allowed = self.ALLOWED_TELEGRAM_USER_IDS
        if not allowed:
            # Strict Fail-Closed: deny all access if whitelist is not explicitly configured
            return False
        return user_id in allowed

settings = Settings()
