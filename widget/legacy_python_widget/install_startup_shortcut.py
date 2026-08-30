"""
CLI utility to install or remove the Notion Tasks Desktop Widget from Windows Startup.
Usage:
    python install_startup_shortcut.py --install
    python install_startup_shortcut.py --remove
    python install_startup_shortcut.py --status
"""
import sys
import argparse
from pathlib import Path
from widget_manager import widget_manager

def main():
    parser = argparse.ArgumentParser(description="Manage Notion Tasks Widget Windows Startup Shortcut")
    parser.add_argument("--install", action="store_true", help="Install widget to Windows Startup")
    parser.add_argument("--remove", action="store_true", help="Remove widget from Windows Startup")
    parser.add_argument("--status", action="store_true", help="Check current startup status")

    args = parser.parse_args()
    shortcut_path = widget_manager.get_startup_shortcut_path()

    if args.install:
        success = widget_manager.set_start_with_windows(True)
        if success:
            print(f"[SUCCESS] Notion Tasks Widget installed to Startup: {shortcut_path}")
        else:
            print("[ERROR] Failed to install startup shortcut.")
    elif args.remove:
        success = widget_manager.set_start_with_windows(False)
        if success:
            print(f"[SUCCESS] Notion Tasks Widget removed from Startup.")
        else:
            print("[ERROR] Failed to remove startup shortcut.")
    else:
        is_installed = shortcut_path.exists()
        print(f"Startup Shortcut Status: {'INSTALLED' if is_installed else 'NOT INSTALLED'}")
        print(f"Path: {shortcut_path}")
        print(f"Config Setting: {widget_manager.config.get('start_with_windows', False)}")

if __name__ == "__main__":
    main()
