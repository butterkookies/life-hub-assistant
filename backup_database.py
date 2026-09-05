"""Crash-safe online SQLite backup script for Andrei's Life Hub Assistant."""

import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from config import settings

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

def backup(dest_dir: str = "backups", keep_days: int = 30) -> str:
    source_path = Path(settings.DATABASE_PATH).resolve()
    if not source_path.exists():
        print(f"❌ Error: Database file not found at {source_path}", file=sys.stderr)
        sys.exit(1)

    backup_folder = Path(dest_dir).resolve()
    backup_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_folder / f"life_hub_backup_{timestamp}.db"

    print(f"📦 Starting live SQLite backup of {source_path.name}...")

    # Using SQLite Online Backup API (thread-safe, WAL-safe, consistent point-in-time snapshot)
    source_conn = sqlite3.connect(str(source_path))
    dest_conn = sqlite3.connect(str(backup_file))

    try:
        source_conn.backup(dest_conn)
        dest_conn.close()
        source_conn.close()
        print(f"✅ Backup successfully saved to: {backup_file} ({backup_file.stat().st_size} bytes)")
    except Exception as e:
        dest_conn.close()
        source_conn.close()
        print(f"❌ Backup failed: {e}", file=sys.stderr)
        sys.exit(1)

    return str(backup_file)

if __name__ == "__main__":
    backup()
