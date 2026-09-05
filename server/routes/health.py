"""Health check API routes."""

import sqlite3
from fastapi import APIRouter
from config import settings
from server.database import get_db_path
from server.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["health"])

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint verifying database connectivity and provider configuration."""
    db_ok = False
    try:
        with sqlite3.connect(get_db_path(), timeout=2.0) as conn:
            conn.execute("SELECT 1")
            db_ok = True
    except Exception:
        db_ok = False

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        service="life-hub-assistant",
        version="1.0.0",
        telegram_enabled=settings.ENABLE_TELEGRAM,
        database_ok=db_ok,
        gemini_configured=bool(settings.GEMINI_API_KEY),
        notion_configured=bool(settings.NOTION_API_KEY)
    )
