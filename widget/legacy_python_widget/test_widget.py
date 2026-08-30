"""
Test Suite for Notion Tasks Desktop Widget
Verifies config persistence, cache management, icon generation, Notion task retrieval, and UI component instantiation.
"""
import os
import sys
import unittest
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from widget_manager import widget_manager, DEFAULT_CONFIG
from notion_service import notion_service


class TestWidgetManager(unittest.TestCase):
    def test_config_loading_and_saving(self):
        config = widget_manager.load_config()
        self.assertIsInstance(config, dict)
        self.assertIn("theme", config)
        self.assertIn("auto_refresh_minutes", config)
        self.assertIn("width", config)
        self.assertIn("height", config)

        # Test updating config
        widget_manager.save_config({"test_key": "test_val"})
        reloaded = widget_manager.load_config()
        self.assertEqual(reloaded.get("test_key"), "test_val")

    def test_cache_management(self):
        sample_tasks = [{"id": "t1", "name": "Sample Task 1", "status": "Not started"}]
        sample_projects = {"p1": "Sample Project"}
        widget_manager.save_cache(sample_tasks, sample_projects)

        loaded_cache = widget_manager.load_cache()
        self.assertEqual(len(loaded_cache.get("tasks", [])), 1)
        self.assertEqual(loaded_cache["tasks"][0]["name"], "Sample Task 1")
        self.assertEqual(loaded_cache.get("projects", {}).get("p1"), "Sample Project")

    def test_icon_generation(self):
        icon_img = widget_manager.generate_icon_image(64)
        self.assertEqual(icon_img.size, (64, 64))
        self.assertEqual(icon_img.mode, "RGBA")


class TestNotionTasksSync(unittest.TestCase):
    def test_projects_map_retrieval(self):
        proj_map = notion_service.get_projects_map()
        self.assertIsInstance(proj_map, dict)
        self.assertGreater(len(proj_map), 0, "Should retrieve accessible Notion projects")
        print(f"[TEST] Retrieved {len(proj_map)} project mappings.")

    def test_tasks_for_day_retrieval(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        tasks = notion_service.get_tasks_for_day(today_str)
        self.assertIsInstance(tasks, list)
        print(f"[TEST] Retrieved {len(tasks)} tasks for {today_str}.")
        for t in tasks[:3]:
            self.assertIn("id", t)
            self.assertIn("name", t)
            self.assertIn("status", t)
            self.assertIn("project_name", t)


class TestWidgetUIInitialization(unittest.TestCase):
    def test_desktop_widget_instantiation(self):
        import customtkinter as ctk
        from desktop_widget import NotionDesktopWidget, TaskCard

        app = NotionDesktopWidget()
        self.assertIsNotNone(app)
        self.assertEqual(app.title(), "Notion Tasks - Home Screen Widget")
        
        # Test creating a mock TaskCard
        mock_task = {
            "id": "mock_id",
            "name": "Unit Test Task",
            "status": "In progress",
            "project_name": "Test Suite",
            "priority": "High",
            "url": "https://notion.so/test"
        }
        card = TaskCard(
            app.task_scroll,
            task=mock_task,
            on_status_toggle=lambda t, s: None,
            on_open_url=lambda u: None,
            theme="dark"
        )
        self.assertIsNotNone(card)
        
        # Clean up
        if app.tray_icon:
            app.tray_icon.stop()
        app.destroy()


if __name__ == "__main__":
    unittest.main()
