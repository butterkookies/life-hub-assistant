import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw

logger = logging.getLogger("widget_manager")

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "widget_config.json"
CACHE_FILE = BASE_DIR / "widget_cache.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "x": 100,
    "y": 100,
    "width": 400,
    "height": 620,
    "theme": "dark",  # "dark" | "light" | "system"
    "always_on_top": False,
    "pinned_to_desktop": False,
    "auto_refresh_minutes": 5,
    "show_completed": True,
    "opacity": 0.96,
    "filter_mode": "today",  # "today" | "active" | "all"
    "start_with_windows": False,
}

class WidgetManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from disk with fallback to defaults."""
        config = dict(DEFAULT_CONFIG)
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    if isinstance(saved, dict):
                        config.update(saved)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        return config

    def save_config(self, updates: Optional[Dict[str, Any]] = None):
        """Save current or updated configuration to disk."""
        if updates:
            self.config.update(updates)
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def load_cache(self) -> Dict[str, Any]:
        """Load cached tasks and project map for instant rendering."""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
        return {"tasks": [], "projects": {}, "last_synced": None}

    def save_cache(self, tasks: List[Dict[str, Any]], projects: Dict[str, str]):
        """Save tasks and projects map to disk."""
        try:
            payload = {
                "tasks": tasks,
                "projects": projects,
                "last_synced": datetime.now().isoformat()
            }
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    @staticmethod
    def get_startup_shortcut_path() -> Path:
        """Return the path to the startup shortcut in Windows."""
        appdata = os.getenv("APPDATA")
        if appdata:
            startup_dir = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        else:
            startup_dir = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        return startup_dir / "NotionTasksWidget.lnk"

    def set_start_with_windows(self, enable: bool) -> bool:
        """Create or remove Windows startup shortcut."""
        shortcut_path = self.get_startup_shortcut_path()
        self.config["start_with_windows"] = enable
        self.save_config()

        if not enable:
            if shortcut_path.exists():
                try:
                    shortcut_path.unlink()
                    logger.info("Removed startup shortcut.")
                    return True
                except Exception as e:
                    logger.error(f"Failed to remove startup shortcut: {e}")
                    return False
            return True

        # Create shortcut
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            
            # Use pythonw.exe to run silently without console
            python_dir = Path(sys.executable).parent
            pythonw_exe = python_dir / "pythonw.exe"
            if not pythonw_exe.exists():
                pythonw_exe = Path(sys.executable)

            target_script = BASE_DIR / "run_widget.pyw"
            shortcut.Targetpath = str(pythonw_exe)
            shortcut.Arguments = f'"{target_script}"'
            shortcut.WorkingDirectory = str(BASE_DIR)
            shortcut.Description = "Notion Tasks Desktop Widget"
            shortcut.save()
            logger.info(f"Created startup shortcut at {shortcut_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create startup shortcut with WScript.Shell: {e}")
            # Fallback: create a .vbs runner in startup folder
            try:
                vbs_path = shortcut_path.with_suffix(".vbs")
                script_path = BASE_DIR / "run_widget.pyw"
                pythonw = str(Path(sys.executable).parent / "pythonw.exe")
                vbs_content = f'Set WshShell = CreateObject("WScript.Shell")\nWshShell.Run """{pythonw}""" & " """{script_path}""", 0, False\n'
                with open(vbs_path, "w", encoding="utf-8") as f:
                    f.write(vbs_content)
                logger.info(f"Created startup VBS runner at {vbs_path}")
                return True
            except Exception as e2:
                logger.error(f"Fallback startup creation also failed: {e2}")
                return False

    @staticmethod
    def generate_icon_image(size: int = 64) -> Image.Image:
        """Generate a sleek Notion-styled icon with a checkmark badge."""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Rounded background square
        margin = max(2, size // 16)
        radius = max(4, size // 5)
        # Gradient or solid dark modern slate background
        draw.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=radius,
            fill=(24, 24, 27, 255),
            outline=(63, 63, 70, 255),
            width=max(1, size // 32)
        )

        # Notion-style "N" or modern task check symbol
        # Let's draw an energetic task checkmark & list lines
        accent_color = (59, 130, 246, 255) # Blue accent
        check_color = (16, 185, 129, 255) # Emerald green
        
        # Checkmark
        p1 = (size * 0.28, size * 0.50)
        p2 = (size * 0.44, size * 0.68)
        p3 = (size * 0.74, size * 0.32)
        draw.line([p1, p2, p3], fill=check_color, width=max(2, size // 10), joint="curve")

        return img

widget_manager = WidgetManager()
