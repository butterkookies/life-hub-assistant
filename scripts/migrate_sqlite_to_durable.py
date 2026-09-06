"""Import a Life Hub SQLite snapshot into configured PostgreSQL and R2 services."""

import argparse
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings
from server.database import close_db, get_db, init_db
from server.storage import object_storage


TABLE_COLUMNS = {
    "users": ["id", "username", "created_at"],
    "conversations": ["id", "user_id", "agent_id", "title", "created_at", "updated_at"],
    "messages": [
        "id", "conversation_id", "user_id", "client_message_id", "role", "content",
        "status", "error_message", "tool_activity_json", "created_at",
    ],
    "push_subscriptions": ["id", "user_id", "endpoint", "p256dh", "auth", "user_agent", "created_at"],
    "briefing_deliveries": ["id", "delivery_date", "channel", "recipient", "status", "delivered_at"],
}


def rows(source: sqlite3.Connection, table: str, columns: Iterable[str]) -> list[dict[str, Any]]:
    names = list(columns)
    result = source.execute(f"SELECT {', '.join(names)} FROM {table}").fetchall()
    return [dict(zip(names, row)) for row in result]


def upsert(target, table: str, values: dict[str, Any], conflict: str = "id") -> None:
    columns = list(values)
    assignments = ", ".join(f"{column} = excluded.{column}" for column in columns if column != conflict)
    placeholders = ", ".join("?" for _ in columns)
    target.execute(
        f"""
        INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})
        ON CONFLICT({conflict}) DO UPDATE SET {assignments}
        """,
        tuple(values[column] for column in columns),
    )


def migrate(source_path: Path, dry_run: bool) -> dict[str, int]:
    if not source_path.exists():
        raise FileNotFoundError(source_path)

    source = sqlite3.connect(str(source_path))
    counts: dict[str, int] = {}
    try:
        for table, columns in TABLE_COLUMNS.items():
            counts[table] = len(rows(source, table, columns))
        attachment_columns = [
            "id", "conversation_id", "message_id", "user_id", "filename", "file_path",
            "mime_type", "size_bytes", "created_at",
        ]
        attachments = rows(source, "attachments", attachment_columns)
        counts["attachments"] = len(attachments)
        if dry_run:
            return counts

        if not settings.DATABASE_URL:
            raise RuntimeError("DATABASE_URL must point to the destination PostgreSQL database")
        if attachments and not object_storage.is_remote():
            raise RuntimeError("Complete R2 configuration is required when the snapshot contains attachments")

        init_db()
        if attachments:
            object_storage.validate()
        with get_db() as target:
            for table in ("users", "conversations", "messages"):
                for value in rows(source, table, TABLE_COLUMNS[table]):
                    upsert(target, table, value)

            for value in attachments:
                old_path = Path(str(value["file_path"]))
                if not old_path.is_absolute():
                    old_path = (source_path.parent / old_path).resolve()
                if not old_path.exists():
                    print(f"Skipping missing attachment file: {value['filename']}")
                    continue
                key = object_storage.attachment_key(value["user_id"], value["id"], value["filename"])
                object_storage.put_bytes(key, old_path.read_bytes(), value["mime_type"])
                value["file_path"] = key
                upsert(target, "attachments", value)

            for value in rows(source, "push_subscriptions", TABLE_COLUMNS["push_subscriptions"]):
                upsert(target, "push_subscriptions", value, conflict="endpoint")
            for value in rows(source, "briefing_deliveries", TABLE_COLUMNS["briefing_deliveries"]):
                columns = list(value)
                target.execute(
                    f"""
                    INSERT INTO briefing_deliveries ({', '.join(columns)})
                    VALUES ({', '.join('?' for _ in columns)})
                    ON CONFLICT(delivery_date, channel, recipient) DO UPDATE SET
                        status = excluded.status, delivered_at = excluded.delivered_at
                    """,
                    tuple(value[column] for column in columns),
                )
        return counts
    finally:
        source.close()
        close_db()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", default="data/life_hub.db")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    counts = migrate(Path(args.source).resolve(), args.dry_run)
    prefix = "Would import" if args.dry_run else "Imported"
    print(prefix + ": " + ", ".join(f"{table}={count}" for table, count in counts.items()))
    print("Sessions and pending scans are intentionally excluded.")


if __name__ == "__main__":
    main()
