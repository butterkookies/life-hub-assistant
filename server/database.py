"""SQLite development and PostgreSQL production persistence."""

import contextlib
import sqlite3
from pathlib import Path
from typing import Any, Generator, Sequence

from config import settings


TABLES_SQL = """
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

CREATE TABLE IF NOT EXISTS briefing_runs (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    delivery_date TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    error_message TEXT,
    PRIMARY KEY(user_id, delivery_date)
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS object_cleanup_queue (
    object_key TEXT PRIMARY KEY,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS storage_objects (
    object_key TEXT PRIMARY KEY,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS storage_usage_daily (
    usage_date TEXT NOT NULL,
    metric TEXT NOT NULL,
    operation_count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(usage_date, metric)
);

CREATE INDEX IF NOT EXISTS idx_storage_usage_metric_date
    ON storage_usage_daily(metric, usage_date);

CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conv_created ON messages(conversation_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_messages_client_id ON messages(conversation_id, client_message_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_messages_client_id
    ON messages(conversation_id, client_message_id)
    WHERE client_message_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_sessions_user_expires ON sessions(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_pending_scans_user ON pending_image_scans(user_id, expires_at);
CREATE INDEX IF NOT EXISTS idx_push_user ON push_subscriptions(user_id);
"""

SQLITE_SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
""" + TABLES_SQL


def _postgres_sql(sql: str) -> str:
    """Convert the project's DB-API qmark placeholders for psycopg."""
    return sql.replace("?", "%s")


class DatabaseConnection:
    """Small common surface used by SQLite and psycopg connections."""

    def __init__(self, raw: Any, postgres: bool = False):
        self.raw = raw
        self.postgres = postgres

    def execute(self, sql: str, params: Sequence[Any] = ()):
        statement = _postgres_sql(sql) if self.postgres else sql
        return self.raw.execute(statement, tuple(params))

    def commit(self) -> None:
        self.raw.commit()

    def rollback(self) -> None:
        self.raw.rollback()


def is_postgres() -> bool:
    return bool(settings.DATABASE_URL)


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


def close_db() -> None:
    """Retained for lifecycle symmetry; PostgreSQL connections close per use."""


def init_db() -> None:
    """Initialize the selected database and ensure the primary user exists."""
    get_upload_dir()
    if is_postgres():
        with get_db() as conn:
            for statement in TABLES_SQL.split(";"):
                if statement.strip():
                    conn.execute(statement)
            conn.execute(
                """
                INSERT INTO users (id, username, created_at)
                VALUES ('andrei-main', 'andrei', CURRENT_TIMESTAMP::text)
                ON CONFLICT(id) DO NOTHING
                """
            )
            conn.execute(
                """
                INSERT INTO schema_migrations (version, applied_at)
                VALUES (1, CURRENT_TIMESTAMP::text)
                ON CONFLICT(version) DO NOTHING
                """
            )
        return

    db_path = get_db_path()
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SQLITE_SCHEMA_SQL)
        conn.execute(
            """
            INSERT INTO users (id, username, created_at)
            VALUES ('andrei-main', 'andrei', datetime('now'))
            ON CONFLICT(id) DO NOTHING
            """
        )
        conn.execute(
            """
            INSERT INTO schema_migrations (version, applied_at)
            VALUES (1, datetime('now'))
            ON CONFLICT(version) DO NOTHING
            """
        )
        conn.commit()


@contextlib.contextmanager
def get_db() -> Generator[DatabaseConnection, None, None]:
    """Yield a transactional connection with mapping-style result rows."""
    if is_postgres():
        from psycopg import connect
        from psycopg.rows import dict_row

        with connect(
            settings.DATABASE_URL,
            connect_timeout=60,
            row_factory=dict_row,
        ) as raw:
            conn = DatabaseConnection(raw, postgres=True)
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return

    db_path = get_db_path()
    raw = sqlite3.connect(db_path, timeout=10.0)
    raw.row_factory = sqlite3.Row
    raw.execute("PRAGMA foreign_keys = ON")
    conn = DatabaseConnection(raw)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        raw.close()
