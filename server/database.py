"""SQLite persistence layer for Andrei's Life Hub Assistant."""

import contextlib
import os
import sqlite3
from pathlib import Path
from typing import Generator
from config import settings

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL DEFAULT 'notion',
    title TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    client_message_id TEXT,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    error_message TEXT,
    tool_activity_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attachments (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    message_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pending_image_scans (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    image_path TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    awaiting_correction INTEGER NOT NULL DEFAULT 0,
    shown_conflicts_json TEXT,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS push_subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint TEXT UNIQUE NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    user_agent TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS briefing_deliveries (
    id TEXT PRIMARY KEY,
    delivery_date TEXT NOT NULL,
    channel TEXT NOT NULL,
    recipient TEXT NOT NULL,
    status TEXT NOT NULL,
    delivered_at TEXT NOT NULL,
    UNIQUE(delivery_date, channel, recipient)
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conv_created ON messages(conversation_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_messages_client_id ON messages(conversation_id, client_message_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_expires ON sessions(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_pending_scans_user ON pending_image_scans(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_push_user ON push_subscriptions(user_id);
"""

def get_db_path() -> str:
    path = settings.DATABASE_PATH
    db_file = Path(path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    return str(db_file.resolve())

def get_upload_dir() -> str:
    path = settings.UPLOAD_DIR
    upload_dir = Path(path)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return str(upload_dir.resolve())

def init_db() -> None:
    """Initialize SQLite database with schema and ensure default user exists."""
    db_path = get_db_path()
    get_upload_dir()
    
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        # Ensure standard primary user exists
        conn.execute(
            """
            INSERT OR IGNORE INTO users (id, username, created_at)
            VALUES ('andrei-main', 'andrei', datetime('now'))
            """
        )
        conn.commit()

@contextlib.contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite connections with row factory and foreign keys."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
