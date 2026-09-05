"""Restore SQLite database from backup for Andrei's Life Hub Assistant."""

import argparse
import os
import shutil
import sqlite3
import sys
from pathlib import Path
from config import settings

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

def restore(backup_path: str = ""):
    target_path = Path(settings.DATABASE_PATH).resolve()

    if not backup_path:
        # Pick the most recent backup from backups/
        backup_folder = Path("backups").resolve()
        if not backup_folder.exists():
            print("❌ Error: No backups directory found.", file=sys.stderr)
            sys.exit(1)
        backups = sorted(backup_folder.glob("life_hub_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not backups:
            print("❌ Error: No backup files found in backups/", file=sys.stderr)
            sys.exit(1)
        backup_file = backups[0]
    else:
        backup_file = Path(backup_path).resolve()
        if not backup_file.exists():
            print(f"❌ Error: Backup file not found at {backup_file}", file=sys.stderr)
            sys.exit(1)

    print(f"🔄 Restoring database from: {backup_file}")
    print(f"🎯 Target location: {target_path}")

    # Make target directory
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Perform restore using SQLite backup API
    src = sqlite3.connect(str(backup_file))
    dst = sqlite3.connect(str(target_path))
    try:
        src.backup(dst)
        src.close()
        dst.close()
        print("✅ Database successfully restored!")
    except Exception as e:
        src.close()
        dst.close()
        print(f"❌ Restore failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore Life Hub database from backup")
    parser.add_argument("-f", "--file", help="Path to backup .db file (defaults to most recent)")
    args = parser.parse_args()
    restore(args.file or "")
