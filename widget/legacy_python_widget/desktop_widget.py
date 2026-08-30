"""
Notion Tasks - Modern Windows Desktop Widget
A sleek, customizable desktop widget for Windows showing today's tasks from Notion.
Supports live sync, instant check-off, quick task creation, and system tray integration.
"""

import os
import sys
import time
import json
import logging
import webbrowser
import threading
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

try:
    import pystray
except ImportError:
    pystray = None

# Ensure current directory is in sys.path
BASE_DIR = Path(__file__).parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from notion_service import notion_service
from widget_manager import widget_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("desktop_widget")

# Theme & Color Palette (Modern Windows 11 Dark / Light)
PALETTE = {
    "dark": {
        "bg": "#18181b",               # Zinc 900
        "card_bg": "#27272a",          # Zinc 800
        "card_hover": "#3f3f46",       # Zinc 700
        "card_done": "#1f2937",        # Muted Dark
        "header_bg": "#202024",        # Header bar
        "border": "#3f3f46",           # Zinc 700
        "text_primary": "#f4f4f5",     # Zinc 100
        "text_secondary": "#a1a1aa",   # Zinc 400
        "text_muted": "#71717a",       # Zinc 500
        "accent": "#3b82f6",           # Blue 500
        "accent_hover": "#2563eb",     # Blue 600
        "done": "#10b981",             # Emerald 500
        "done_hover": "#059669",       # Emerald 600
        "in_progress": "#f59e0b",      # Amber 500
        "not_started": "#6b7280",      # Gray 500
        "high_priority": "#ef4444",    # Red 500
        "tag_bg": "#312e81",           # Indigo 900
        "tag_text": "#c7d2fe",         # Indigo 200
        "progress_bg": "#3f3f46",
    },
    "light": {
        "bg": "#f4f4f5",
        "card_bg": "#ffffff",
        "card_hover": "#f0f0f2",
        "card_done": "#f3f4f6",
        "header_bg": "#e4e4e7",
        "border": "#e4e4e7",
        "text_primary": "#18181b",
        "text_secondary": "#52525b",
        "text_muted": "#a1a1aa",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "done": "#059669",
        "done_hover": "#047857",
        "in_progress": "#d97706",
        "not_started": "#9ca3af",
        "high_priority": "#dc2626",
        "tag_bg": "#e0e7ff",
        "tag_text": "#3730a3",
        "progress_bg": "#e4e4e7",
    }
}

PROJECT_COLORS = [
    ("#1e3a8a", "#93c5fd"),  # Blue
    ("#14532d", "#86efac"),  # Green
    ("#701a75", "#f0abfc"),  # Fuchsia
    ("#581c87", "#d8b4fe"),  # Purple
    ("#7c2d12", "#fdba74"),  # Orange
    ("#134e4a", "#5eead4"),  # Teal
    ("#831843", "#f9a8d4"),  # Pink
]

def get_project_color(project_name: str) -> tuple:
    """Deterministically assign a color pair to a project name."""
    if not project_name:
        return ("#27272a", "#d4d4d8")
    h = sum(ord(c) for c in project_name)
    return PROJECT_COLORS[h % len(PROJECT_COLORS)]


class TaskCard(ctk.CTkFrame):
    """Interactive card representing a single task."""
    def __init__(self, master, task: Dict[str, Any], on_status_toggle, on_open_url, theme: str = "dark", **kwargs):
        self.task = task
        self.on_status_toggle = on_status_toggle
        self.on_open_url = on_open_url
        self.current_theme = theme
        self.palette = PALETTE.get(theme, PALETTE["dark"])

        is_done = str(task.get("status", "")).lower() == "done"
        card_bg = self.palette["card_done"] if is_done else self.palette["card_bg"]

        super().__init__(
            master,
            fg_color=card_bg,
            corner_radius=10,
            border_width=1,
            border_color=self.palette["border"],
            **kwargs
        )

        self.grid_columnconfigure(1, weight=1)
        self._build_ui()

    def _build_ui(self):
        status = str(self.task.get("status", "Not started")).strip()
        is_done = status.lower() == "done"
        is_in_progress = status.lower() in ("in progress", "in-progress", "doing")

        # 1. Left: Status / Checkbox button
        if is_done:
            btn_text = "✓"
            btn_fg = self.palette["done"]
            btn_hover = self.palette["done_hover"]
            text_color = "#ffffff"
        elif is_in_progress:
            btn_text = "●"
            btn_fg = self.palette["in_progress"]
            btn_hover = "#d97706"
            text_color = "#ffffff"
        else:
            btn_text = "○"
            btn_fg = "transparent"
            btn_hover = self.palette["card_hover"]
            text_color = self.palette["text_muted"]

        self.check_btn = ctk.CTkButton(
            self,
            text=btn_text,
            width=28,
            height=28,
            corner_radius=14,
            fg_color=btn_fg,
            hover_color=btn_hover,
            text_color=text_color,
            font=ctk.CTkFont(size=14, weight="bold"),
            border_width=1 if not is_done and not is_in_progress else 0,
            border_color=self.palette["text_muted"],
            command=self._on_check_clicked
        )
        self.check_btn.grid(row=0, column=0, rowspan=2, padx=(10, 8), pady=10, sticky="n")

        # 2. Middle: Task Title
        title_text = self.task.get("name", "Untitled Task")
        title_color = self.palette["text_muted"] if is_done else self.palette["text_primary"]
        
        # Format strikethrough text for Done items
        if is_done:
            display_title = "".join(c + "\u0336" for c in title_text)
        else:
            display_title = title_text

        self.title_lbl = ctk.CTkLabel(
            self,
            text=display_title,
            font=ctk.CTkFont(size=13, weight="normal" if is_done else "bold"),
            text_color=title_color,
            anchor="w",
            justify="left",
            wraplength=240
        )
        self.title_lbl.grid(row=0, column=1, padx=(0, 5), pady=(8, 2), sticky="w")
        self.title_lbl.bind("<Button-1>", lambda e: self._on_card_clicked())

        # 3. Middle bottom: Tags Row (Project pill + Status badge + Priority)
        tags_frame = ctk.CTkFrame(self, fg_color="transparent")
        tags_frame.grid(row=1, column=1, padx=(0, 5), pady=(0, 8), sticky="w")

        project_name = self.task.get("project_name", "Personal")
        proj_bg, proj_fg = get_project_color(project_name)

        self.proj_badge = ctk.CTkLabel(
            tags_frame,
            text=f"📁 {project_name}",
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=proj_bg,
            text_color=proj_fg,
            corner_radius=6,
            padx=6,
            pady=2
        )
        self.proj_badge.pack(side="left", padx=(0, 5))

        # Status text pill
        status_color = self.palette["done"] if is_done else (self.palette["in_progress"] if is_in_progress else self.palette["text_muted"])
        self.status_badge = ctk.CTkLabel(
            tags_frame,
            text=status,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            text_color=status_color
        )
        self.status_badge.pack(side="left", padx=(0, 5))

        # Priority badge if High
        priority = str(self.task.get("priority", "Normal"))
        if priority.lower() in ("high", "urgent", "p1"):
            self.priority_badge = ctk.CTkLabel(
                tags_frame,
                text="🔥 High",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=self.palette["high_priority"],
                text_color="#ffffff",
                corner_radius=6,
                padx=4,
                pady=1
            )
            self.priority_badge.pack(side="left", padx=(0, 5))

        # 4. Right: Open in Notion button
        url = self.task.get("url")
        if url:
            self.open_btn = ctk.CTkButton(
                self,
                text="↗",
                width=24,
                height=24,
                corner_radius=12,
                fg_color="transparent",
                hover_color=self.palette["card_hover"],
                text_color=self.palette["text_secondary"],
                font=ctk.CTkFont(size=12, weight="bold"),
                command=lambda: self.on_open_url(url)
            )
            self.open_btn.grid(row=0, column=2, rowspan=2, padx=(2, 8), pady=10, sticky="e")

    def _on_check_clicked(self):
        current_status = str(self.task.get("status", "Not started")).strip()
        # Cycle: Not started -> In progress -> Done -> Not started
        if current_status.lower() == "done":
            new_status = "Not started"
        elif current_status.lower() in ("in progress", "in-progress", "doing"):
            new_status = "Done"
        else:
            new_status = "Done"
        
        self.on_status_toggle(self.task, new_status)

    def _on_card_clicked(self):
        url = self.task.get("url")
        if url:
            self.on_open_url(url)


class QuickAddTaskDialog(ctk.CTkToplevel):
    """Modal dialog for quickly adding a new task to Notion for today."""
    def __init__(self, parent, projects_map: Dict[str, str], on_task_created):
        super().__init__(parent)
        self.parent = parent
        self.projects_map = projects_map
        self.on_task_created = on_task_created

        self.title("Quick Add Task - Notion")
        self.geometry("380x320")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Center relative to parent
        try:
            x = parent.winfo_x() + 20
            y = parent.winfo_y() + 60
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self._build_ui()
        self.transient(parent)
        self.grab_set()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Title Header
        header = ctk.CTkLabel(
            container,
            text="✨ Add Task for Today",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w"
        )
        header.pack(fill="x", pady=(0, 15))

        # Task Name
        ctk.CTkLabel(container, text="Task Name", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
        self.name_entry = ctk.CTkEntry(container, placeholder_text="What needs to be done?", height=35)
        self.name_entry.pack(fill="x", pady=(3, 12))
        self.name_entry.focus()
        self.name_entry.bind("<Return>", lambda e: self._submit())

        # Project Selector
        ctk.CTkLabel(container, text="Project (Optional)", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
        proj_names = ["(None / Personal)"] + sorted(list(set(self.projects_map.values())))
        self.proj_combo = ctk.CTkComboBox(container, values=proj_names, height=35)
        self.proj_combo.set(proj_names[0])
        self.proj_combo.pack(fill="x", pady=(3, 12))

        # Priority & Due Date row
        row_frame = ctk.CTkFrame(container, fg_color="transparent")
        row_frame.pack(fill="x", pady=(0, 15))

        prio_col = ctk.CTkFrame(row_frame, fg_color="transparent")
        prio_col.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkLabel(prio_col, text="Priority", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
        self.prio_combo = ctk.CTkComboBox(prio_col, values=["Normal", "High", "Low"], height=32)
        self.prio_combo.set("Normal")
        self.prio_combo.pack(fill="x", pady=(3, 0))

        date_col = ctk.CTkFrame(row_frame, fg_color="transparent")
        date_col.pack(side="left", fill="x", expand=True, padx=(5, 0))
        ctk.CTkLabel(date_col, text="Do Date", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
        today_str = datetime.now().strftime("%Y-%m-%d")
        self.date_entry = ctk.CTkEntry(date_col, height=32)
        self.date_entry.insert(0, today_str)
        self.date_entry.pack(fill="x", pady=(3, 0))

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self.destroy,
            width=100
        )
        cancel_btn.pack(side="left")

        self.submit_btn = ctk.CTkButton(
            btn_frame,
            text="Create Task",
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self._submit,
            width=140
        )
        self.submit_btn.pack(side="right")

    def _submit(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Task Name Required", "Please enter a task name.", parent=self)
            return

        selected_proj_name = self.proj_combo.get()
        project_id = None
        if selected_proj_name and selected_proj_name != "(None / Personal)":
            for pid, pname in self.projects_map.items():
                if pname == selected_proj_name:
                    project_id = pid
                    break

        priority = self.prio_combo.get()
        do_date = self.date_entry.get().strip() or datetime.now().strftime("%Y-%m-%d")

        self.submit_btn.configure(state="disabled", text="Creating...")
        self.on_task_created(name, project_id, selected_proj_name, priority, do_date)
        self.destroy()


class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog for customizing widget behavior and appearance."""
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.parent = parent
        self.on_save = on_save
        self.config = dict(widget_manager.config)

        self.title("Widget Settings")
        self.geometry("380x440")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        try:
            x = parent.winfo_x() + 20
            y = parent.winfo_y() + 60
            self.geometry(f"+{x}+{y}")
        except Exception:
            pass

        self._build_ui()
        self.transient(parent)
        self.grab_set()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="⚙️ Preferences & Behavior", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", pady=(0, 15))

        # 1. Theme
        ctk.CTkLabel(container, text="Theme Appearance", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
        self.theme_combo = ctk.CTkComboBox(container, values=["dark", "light", "system"], height=32)
        self.theme_combo.set(self.config.get("theme", "dark"))
        self.theme_combo.pack(fill="x", pady=(3, 12))

        # 2. Auto-refresh
        ctk.CTkLabel(container, text="Auto-Refresh Interval", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
        self.refresh_combo = ctk.CTkComboBox(container, values=["1 minute", "3 minutes", "5 minutes", "15 minutes", "Manual only"], height=32)
        curr_interval = self.config.get("auto_refresh_minutes", 5)
        if curr_interval == 1:
            self.refresh_combo.set("1 minute")
        elif curr_interval == 3:
            self.refresh_combo.set("3 minutes")
        elif curr_interval == 15:
            self.refresh_combo.set("15 minutes")
        elif curr_interval <= 0:
            self.refresh_combo.set("Manual only")
        else:
            self.refresh_combo.set("5 minutes")
        self.refresh_combo.pack(fill="x", pady=(3, 12))

        # 3. Opacity Slider
        ctk.CTkLabel(container, text=f"Widget Opacity ({int(self.config.get('opacity', 0.96)*100)}%)", font=ctk.CTkFont(size=12, weight="bold"), anchor="w").pack(fill="x")
        self.opacity_slider = ctk.CTkSlider(container, from_=0.6, to=1.0, number_of_steps=20)
        self.opacity_slider.set(self.config.get("opacity", 0.96))
        self.opacity_slider.pack(fill="x", pady=(3, 12))

        # 4. Toggles
        self.topmost_var = ctk.BooleanVar(value=self.config.get("always_on_top", False))
        self.topmost_cb = ctk.CTkCheckBox(container, text="Always on Top (Float above windows)", variable=self.topmost_var)
        self.topmost_cb.pack(fill="x", pady=6)

        self.show_done_var = ctk.BooleanVar(value=self.config.get("show_completed", True))
        self.show_done_cb = ctk.CTkCheckBox(container, text="Show Completed Tasks in Today view", variable=self.show_done_var)
        self.show_done_cb.pack(fill="x", pady=6)

        self.startup_var = ctk.BooleanVar(value=self.config.get("start_with_windows", False))
        self.startup_cb = ctk.CTkCheckBox(container, text="Launch automatically on Windows startup", variable=self.startup_var)
        self.startup_cb.pack(fill="x", pady=6)

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))

        cancel_btn = ctk.CTkButton(btn_frame, text="Cancel", fg_color="transparent", border_width=1, command=self.destroy, width=100)
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(btn_frame, text="Save Settings", fg_color="#2563eb", hover_color="#1d4ed8", command=self._save, width=140)
        save_btn.pack(side="right")

    def _save(self):
        theme = self.theme_combo.get()
        ref_text = self.refresh_combo.get()
        if "1 min" in ref_text:
            ref_min = 1
        elif "3 min" in ref_text:
            ref_min = 3
        elif "15 min" in ref_text:
            ref_min = 15
        elif "Manual" in ref_text:
            ref_min = 0
        else:
            ref_min = 5

        opacity = round(self.opacity_slider.get(), 2)
        topmost = self.topmost_var.get()
        show_done = self.show_done_var.get()
        start_win = self.startup_var.get()

        updates = {
            "theme": theme,
            "auto_refresh_minutes": ref_min,
            "opacity": opacity,
            "always_on_top": topmost,
            "show_completed": show_done,
            "start_with_windows": start_win
        }

        widget_manager.save_config(updates)
        widget_manager.set_start_with_windows(start_win)

        self.on_save(updates)
        self.destroy()


class NotionDesktopWidget(ctk.CTk):
    """Main Windows Home Screen Widget Application."""
    def __init__(self):
        super().__init__()

        self.config = widget_manager.load_config()
        self.current_theme = self.config.get("theme", "dark")
        ctk.set_appearance_mode(self.current_theme)
        ctk.set_default_color_theme("blue")

        self.tasks: List[Dict[str, Any]] = []
        self.projects_map: Dict[str, str] = {}
        self.is_syncing = False
        self.filter_mode = self.config.get("filter_mode", "today")

        # Window Configuration
        self.title("Notion Tasks - Home Screen Widget")
        w = self.config.get("width", 400)
        h = self.config.get("height", 620)
        x = self.config.get("x", 100)
        y = self.config.get("y", 100)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.minsize(340, 480)

        # Set Opacity & Topmost
        self.attributes("-alpha", self.config.get("opacity", 0.96))
        if self.config.get("always_on_top", False):
            self.attributes("-topmost", True)

        # Set Window Icon
        try:
            icon_img = widget_manager.generate_icon_image(64)
            self.tk_icon = ImageTk.PhotoImage(icon_img)
            self.iconphoto(True, self.tk_icon)
        except Exception as e:
            logger.warning(f"Could not set window icon: {e}")

        # Drag Window Support Variables
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Build UI
        self._build_ui()

        # Window Position Saving on Move / Resize
        self.bind("<Configure>", self._on_window_configure)
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        # Load Cache first for instant startup
        self._load_cached_data()

        # Start System Tray in background thread
        self.tray_icon = None
        self._setup_system_tray()

        # Start background sync with Notion
        self.sync_tasks_async()

        # Start auto-refresh scheduler
        self._schedule_auto_refresh()

    def _build_ui(self):
        self.palette = PALETTE.get(self.current_theme, PALETTE["dark"])
        self.configure(fg_color=self.palette["bg"])

        # Main Root Container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=12, pady=12)

        # 1. Custom Drag Header Bar
        self.header_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.palette["header_bg"],
            corner_radius=12,
            height=60
        )
        self.header_frame.pack(fill="x", pady=(0, 10))
        self.header_frame.pack_propagate(False)

        # Drag handlers on header
        self.header_frame.bind("<Button-1>", self._start_drag)
        self.header_frame.bind("<B1-Motion>", self._on_drag)

        # Left: Title + Date
        header_left = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_left.pack(side="left", padx=12, pady=8)
        header_left.bind("<Button-1>", self._start_drag)
        header_left.bind("<B1-Motion>", self._on_drag)

        title_lbl = ctk.CTkLabel(
            header_left,
            text="📋 Daily Tasks",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=self.palette["text_primary"]
        )
        title_lbl.pack(anchor="w")
        title_lbl.bind("<Button-1>", self._start_drag)
        title_lbl.bind("<B1-Motion>", self._on_drag)

        today_str = datetime.now().strftime("%A, %b %d")
        self.date_lbl = ctk.CTkLabel(
            header_left,
            text=today_str,
            font=ctk.CTkFont(size=11),
            text_color=self.palette["text_secondary"]
        )
        self.date_lbl.pack(anchor="w")
        self.date_lbl.bind("<Button-1>", self._start_drag)
        self.date_lbl.bind("<B1-Motion>", self._on_drag)

        # Right: Quick Action Buttons (+ Add, 🔄 Sync, ⚙️ Settings, — Minimize)
        header_right = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        header_right.pack(side="right", padx=8, pady=8)

        # + Add Task
        self.add_btn = ctk.CTkButton(
            header_right,
            text="+",
            width=28,
            height=28,
            corner_radius=14,
            fg_color=self.palette["accent"],
            hover_color=self.palette["accent_hover"],
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.open_quick_add
        )
        self.add_btn.pack(side="left", padx=3)

        # 🔄 Refresh
        self.refresh_btn = ctk.CTkButton(
            header_right,
            text="🔄",
            width=28,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            hover_color=self.palette["card_hover"],
            text_color=self.palette["text_secondary"],
            font=ctk.CTkFont(size=13),
            command=self.sync_tasks_async
        )
        self.refresh_btn.pack(side="left", padx=3)

        # 📌 Pin / Always on Top toggle
        self.pin_btn = ctk.CTkButton(
            header_right,
            text="📌" if self.config.get("always_on_top", False) else "📍",
            width=28,
            height=28,
            corner_radius=14,
            fg_color=self.palette["card_hover"] if self.config.get("always_on_top", False) else "transparent",
            hover_color=self.palette["card_hover"],
            text_color=self.palette["text_secondary"],
            font=ctk.CTkFont(size=13),
            command=self.toggle_always_on_top
        )
        self.pin_btn.pack(side="left", padx=3)

        # ⚙️ Settings
        self.settings_btn = ctk.CTkButton(
            header_right,
            text="⚙️",
            width=28,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            hover_color=self.palette["card_hover"],
            text_color=self.palette["text_secondary"],
            font=ctk.CTkFont(size=13),
            command=self.open_settings
        )
        self.settings_btn.pack(side="left", padx=3)

        # — Minimize to Tray
        self.min_btn = ctk.CTkButton(
            header_right,
            text="—",
            width=28,
            height=28,
            corner_radius=14,
            fg_color="transparent",
            hover_color=self.palette["card_hover"],
            text_color=self.palette["text_secondary"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.minimize_to_tray
        )
        self.min_btn.pack(side="left", padx=3)

        # 2. Progress Metric Card
        self.stats_card = ctk.CTkFrame(
            self.main_container,
            fg_color=self.palette["card_bg"],
            corner_radius=10,
            border_width=1,
            border_color=self.palette["border"]
        )
        self.stats_card.pack(fill="x", pady=(0, 10), padx=2)

        stats_inner = ctk.CTkFrame(self.stats_card, fg_color="transparent")
        stats_inner.pack(fill="x", padx=12, pady=10)

        stats_top = ctk.CTkFrame(stats_inner, fg_color="transparent")
        stats_top.pack(fill="x", pady=(0, 5))

        self.stats_lbl = ctk.CTkLabel(
            stats_top,
            text="0 of 0 Completed",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.palette["text_primary"]
        )
        self.stats_lbl.pack(side="left")

        self.percent_lbl = ctk.CTkLabel(
            stats_top,
            text="0%",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.palette["accent"]
        )
        self.percent_lbl.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(
            stats_inner,
            height=8,
            corner_radius=4,
            fg_color=self.palette["progress_bg"],
            progress_color=self.palette["done"]
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x")

        # 3. Filter Tabs (Segmented Button)
        self.filter_seg = ctk.CTkSegmentedButton(
            self.main_container,
            values=["Today", "Active", "All"],
            command=self._on_filter_changed,
            height=28,
            corner_radius=8,
            selected_color=self.palette["accent"],
            selected_hover_color=self.palette["accent_hover"],
            unselected_color=self.palette["card_bg"],
            unselected_hover_color=self.palette["card_hover"],
            font=ctk.CTkFont(size=11, weight="bold")
        )
        self.filter_seg.set(self.filter_mode.capitalize())
        self.filter_seg.pack(fill="x", pady=(0, 8), padx=2)

        # 4. Scrollable Task List
        self.task_scroll = ctk.CTkScrollableFrame(
            self.main_container,
            fg_color="transparent",
            corner_radius=8
        )
        self.task_scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # 5. Bottom Status / Sync bar
        self.footer_frame = ctk.CTkFrame(self.main_container, fg_color="transparent", height=20)
        self.footer_frame.pack(fill="x", pady=(6, 0))

        self.sync_status_lbl = ctk.CTkLabel(
            self.footer_frame,
            text="Ready",
            font=ctk.CTkFont(size=10),
            text_color=self.palette["text_muted"],
            anchor="w"
        )
        self.sync_status_lbl.pack(side="left", padx=4)

        self.notion_link_lbl = ctk.CTkLabel(
            self.footer_frame,
            text="🔗 Open Notion",
            font=ctk.CTkFont(size=10),
            text_color=self.palette["accent"],
            cursor="hand2"
        )
        self.notion_link_lbl.pack(side="right", padx=4)
        self.notion_link_lbl.bind("<Button-1>", lambda e: webbrowser.open("https://www.notion.so"))

    def _start_drag(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag(self, event):
        x = self.winfo_x() + (event.x - self._drag_start_x)
        y = self.winfo_y() + (event.y - self._drag_start_y)
        self.geometry(f"+{x}+{y}")

    def _on_window_configure(self, event):
        # Save position when moved or resized
        if event.widget == self:
            x, y = self.winfo_x(), self.winfo_y()
            w, h = self.winfo_width(), self.winfo_height()
            if w > 100 and h > 100:
                self.config["x"] = x
                self.config["y"] = y
                self.config["width"] = w
                self.config["height"] = h

    def toggle_always_on_top(self):
        current = self.config.get("always_on_top", False)
        new_val = not current
        self.config["always_on_top"] = new_val
        self.attributes("-topmost", new_val)
        self.pin_btn.configure(
            text="📌" if new_val else "📍",
            fg_color=self.palette["card_hover"] if new_val else "transparent"
        )
        widget_manager.save_config({"always_on_top": new_val})

    def open_quick_add(self):
        QuickAddTaskDialog(self, self.projects_map, self._handle_create_task)

    def open_settings(self):
        SettingsDialog(self, self._apply_settings_updates)

    def _apply_settings_updates(self, updates: Dict[str, Any]):
        self.config.update(updates)
        if "theme" in updates:
            self.current_theme = updates["theme"]
            ctk.set_appearance_mode(self.current_theme)
            self._rebuild_theme_palette()
        if "opacity" in updates:
            self.attributes("-alpha", updates["opacity"])
        if "always_on_top" in updates:
            self.attributes("-topmost", updates["always_on_top"])
            self.pin_btn.configure(
                text="📌" if updates["always_on_top"] else "📍",
                fg_color=self.palette["card_hover"] if updates["always_on_top"] else "transparent"
            )
        self._render_tasks()

    def _rebuild_theme_palette(self):
        self.palette = PALETTE.get(self.current_theme, PALETTE["dark"])
        self.configure(fg_color=self.palette["bg"])
        self.header_frame.configure(fg_color=self.palette["header_bg"])
        self.stats_card.configure(fg_color=self.palette["card_bg"], border_color=self.palette["border"])
        self.stats_lbl.configure(text_color=self.palette["text_primary"])
        self.progress_bar.configure(fg_color=self.palette["progress_bg"], progress_color=self.palette["done"])
        self.filter_seg.configure(
            selected_color=self.palette["accent"],
            selected_hover_color=self.palette["accent_hover"],
            unselected_color=self.palette["card_bg"],
            unselected_hover_color=self.palette["card_hover"]
        )

    def _on_filter_changed(self, value):
        self.filter_mode = value.lower()
        self.config["filter_mode"] = self.filter_mode
        widget_manager.save_config({"filter_mode": self.filter_mode})
        self._render_tasks()

    def _load_cached_data(self):
        cache = widget_manager.load_cache()
        if cache.get("tasks"):
            self.tasks = cache["tasks"]
            self.projects_map = cache.get("projects", {})
            self._render_tasks()
            last_sync = cache.get("last_synced", "")
            if last_sync:
                try:
                    dt = datetime.fromisoformat(last_sync)
                    self.sync_status_lbl.configure(text=f"Cached: {dt.strftime('%I:%M %p')}")
                except Exception:
                    pass

    def sync_tasks_async(self):
        """Fetch tasks and project map from Notion in a background thread."""
        if self.is_syncing:
            return
        self.is_syncing = True
        self.refresh_btn.configure(state="disabled", text="⏳")
        self.sync_status_lbl.configure(text="Syncing with Notion...")

        def _worker():
            try:
                today_str = datetime.now().strftime("%Y-%m-%d")
                projects = notion_service.get_projects_map()
                tasks = notion_service.get_tasks_for_day(today_str)
                # Success: dispatch to main UI thread
                self.after(0, lambda: self._on_sync_success(tasks, projects))
            except Exception as e:
                logger.error(f"Sync failed: {e}")
                self.after(0, lambda: self._on_sync_error(str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_sync_success(self, tasks: List[Dict[str, Any]], projects: Dict[str, str]):
        self.is_syncing = False
        self.tasks = tasks
        self.projects_map = projects
        self.refresh_btn.configure(state="normal", text="🔄")
        now_str = datetime.now().strftime("%I:%M %p")
        self.sync_status_lbl.configure(text=f"Updated: {now_str}")
        
        # Save to disk cache
        widget_manager.save_cache(tasks, projects)
        self._render_tasks()

    def _on_sync_error(self, err_msg: str):
        self.is_syncing = False
        self.refresh_btn.configure(state="normal", text="🔄")
        self.sync_status_lbl.configure(text=f"Sync error (offline)")
        logger.warning(f"Background sync error: {err_msg}")

    def _render_tasks(self):
        """Render task cards into the scrollable list."""
        for widget in self.task_scroll.winfo_children():
            widget.destroy()

        today_str = datetime.now().strftime("%Y-%m-%d")

        # Filter tasks
        filtered = []
        for t in self.tasks:
            status = str(t.get("status", "Not started")).strip().lower()
            is_done = status == "done"
            t_date = str(t.get("date", ""))

            if self.filter_mode == "today":
                # Only today
                if not self.config.get("show_completed", True) and is_done:
                    continue
                filtered.append(t)
            elif self.filter_mode == "active":
                # In progress or Not started
                if not is_done:
                    filtered.append(t)
            else: # "all"
                filtered.append(t)

        # Update Stats & Progress Bar based on today's tasks
        today_tasks = [t for t in self.tasks if str(t.get("date", "")).startswith(today_str)] or self.tasks
        total_count = len(today_tasks)
        done_count = sum(1 for t in today_tasks if str(t.get("status", "")).lower() == "done")
        
        self.stats_lbl.configure(text=f"{done_count} of {total_count} Completed")
        ratio = (done_count / total_count) if total_count > 0 else 0.0
        self.progress_bar.set(ratio)
        self.percent_lbl.configure(text=f"{int(ratio * 100)}%")

        # Empty state
        if not filtered:
            empty_frame = ctk.CTkFrame(self.task_scroll, fg_color="transparent")
            empty_frame.pack(fill="both", expand=True, pady=40)

            msg = "🎉 All done for today!" if done_count == total_count and total_count > 0 else "No tasks scheduled for today."
            ctk.CTkLabel(
                empty_frame,
                text=msg,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=self.palette["text_secondary"]
            ).pack()

            ctk.CTkButton(
                empty_frame,
                text="+ Add a Task",
                font=ctk.CTkFont(size=12),
                fg_color=self.palette["accent"],
                hover_color=self.palette["accent_hover"],
                command=self.open_quick_add,
                width=120
            ).pack(pady=12)
            return

        # Render Task Cards (sorted: in progress -> not started -> done)
        def sort_key(item):
            st = str(item.get("status", "")).lower()
            if st in ("in progress", "in-progress", "doing"):
                return 0
            elif st == "not started":
                return 1
            else:
                return 2

        sorted_tasks = sorted(filtered, key=sort_key)

        for task in sorted_tasks:
            card = TaskCard(
                self.task_scroll,
                task=task,
                on_status_toggle=self._handle_status_toggle,
                on_open_url=self._handle_open_url,
                theme=self.current_theme
            )
            card.pack(fill="x", pady=4, padx=2)

    def _handle_status_toggle(self, task: Dict[str, Any], new_status: str):
        """Optimistically update UI and sync new status to Notion."""
        task_id = task.get("id")
        old_status = task.get("status")
        task["status"] = new_status
        
        # Immediate UI refresh
        self._render_tasks()
        self.sync_status_lbl.configure(text=f"Updating '{task.get('name')[:15]}...'")

        def _worker():
            try:
                notion_service.update_page_properties(task_id, {"Status": new_status})
                self.after(0, lambda: self.sync_status_lbl.configure(text=f"Saved '{new_status}' to Notion"))
                widget_manager.save_cache(self.tasks, self.projects_map)
            except Exception as e:
                logger.error(f"Status update failed: {e}")
                task["status"] = old_status
                self.after(0, lambda: self._on_status_update_error(task.get("name", "Task"), str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_status_update_error(self, task_name: str, error: str):
        self._render_tasks()
        self.sync_status_lbl.configure(text="Sync failed - reverted")
        messagebox.showerror("Notion Update Failed", f"Could not update task '{task_name}':\n{error}", parent=self)

    def _handle_open_url(self, url: str):
        try:
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"Failed to open URL: {e}")

    def _handle_create_task(self, name: str, project_id: Optional[str], project_name: str, priority: str, do_date: str):
        """Create task in Notion and update UI."""
        self.sync_status_lbl.configure(text=f"Creating '{name[:20]}...'")

        # Optimistic placeholder
        placeholder = {
            "id": f"temp_{int(time.time())}",
            "name": name,
            "date": do_date,
            "status": "Not started",
            "priority": priority,
            "project_id": project_id,
            "project_name": project_name if project_name != "(None / Personal)" else "Personal",
            "url": None,
            "properties": {}
        }
        self.tasks.insert(0, placeholder)
        self._render_tasks()

        def _worker():
            try:
                props = {
                    "Do Date": do_date,
                    "Status": "Not started",
                    "Priority": priority
                }
                if project_id:
                    props["Projects"] = [project_id]

                res = notion_service.create_database_item(
                    database_id="d1527102528783299cac81b9d565b99b",
                    title=name,
                    properties=props
                )
                placeholder["id"] = res.get("id")
                placeholder["url"] = res.get("url")
                self.after(0, lambda: self.sync_status_lbl.configure(text="Task created in Notion!"))
                widget_manager.save_cache(self.tasks, self.projects_map)
                self.after(0, self._render_tasks)
            except Exception as e:
                logger.error(f"Task creation failed: {e}")
                if placeholder in self.tasks:
                    self.tasks.remove(placeholder)
                self.after(0, lambda: self._on_task_create_error(name, str(e)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_task_create_error(self, name: str, err: str):
        self._render_tasks()
        self.sync_status_lbl.configure(text="Failed to create task")
        messagebox.showerror("Task Creation Failed", f"Could not create task '{name}':\n{err}", parent=self)

    def _schedule_auto_refresh(self):
        interval_min = self.config.get("auto_refresh_minutes", 5)
        if interval_min > 0:
            ms = interval_min * 60 * 1000
            self.after(ms, self._on_timer_refresh)

    def _on_timer_refresh(self):
        self.sync_tasks_async()
        self._schedule_auto_refresh()

    # System Tray Integration
    def _setup_system_tray(self):
        if not pystray:
            logger.warning("pystray not installed, system tray disabled.")
            return

        icon_image = widget_manager.generate_icon_image(64)

        menu = pystray.Menu(
            pystray.MenuItem("📋 Show Tasks Widget", self._tray_show_widget, default=True),
            pystray.MenuItem("➕ Add Task for Today...", self._tray_quick_add),
            pystray.MenuItem("🔄 Sync Now", lambda icon, item: self.after(0, self.sync_tasks_async)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("📌 Always on Top", lambda icon, item: self.after(0, self.toggle_always_on_top), checked=lambda item: self.config.get("always_on_top", False)),
            pystray.MenuItem("⚙️ Settings...", lambda icon, item: self.after(0, self.open_settings)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Exit Widget", self._tray_exit)
        )

        self.tray_icon = pystray.Icon("notion_tasks_widget", icon_image, "Notion Tasks Widget", menu)

        def _run_tray():
            try:
                self.tray_icon.run()
            except Exception as e:
                logger.error(f"Tray error: {e}")

        threading.Thread(target=_run_tray, daemon=True).start()

    def _tray_show_widget(self, icon, item):
        self.after(0, self.restore_from_tray)

    def _tray_quick_add(self, icon, item):
        self.after(0, lambda: (self.restore_from_tray(), self.open_quick_add()))

    def _tray_exit(self, icon, item):
        self.after(0, self.exit_app)

    def minimize_to_tray(self):
        """Hide main window and notify user in system tray."""
        self.withdraw()
        if self.tray_icon:
            try:
                self.tray_icon.notify("Notion Tasks is running in the system tray.", "Notion Widget Minimized")
            except Exception:
                pass

    def restore_from_tray(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def exit_app(self):
        """Save settings and cleanly exit."""
        widget_manager.save_config(self.config)
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()
        sys.exit(0)


def main():
    app = NotionDesktopWidget()
    app.mainloop()


if __name__ == "__main__":
    main()
