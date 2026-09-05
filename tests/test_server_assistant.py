"""Tests for shared assistant service, context rehydration, and error sanitization."""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from config import settings
from gemini_agent import gemini_agent
from server.database import get_db, init_db
from server.services.assistant_service import assistant_service
from server.services.conversation_service import conversation_service

class AssistantServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "test_asst.db")
        self.upload_dir = os.path.join(self.temp_dir.name, "uploads")
        os.makedirs(self.upload_dir, exist_ok=True)

        self.env_patch = patch.dict(os.environ, {
            "DATABASE_PATH": self.db_path,
            "UPLOAD_DIR": self.upload_dir,
            "GEMINI_API_KEY": "test-gemini-key",
            "NOTION_API_KEY": "test-notion-key"
        })
        self.env_patch.start()
        init_db()

        self.conv = conversation_service.create_conversation("andrei-main", title="Chat 1")

    def tearDown(self):
        self.env_patch.stop()
        self.temp_dir.cleanup()

    @patch.object(gemini_agent, "process_text_message")
    async def test_text_message_processing_success(self, mock_process_text):
        """Assistant processes user prompt and persists both user and assistant messages."""
        mock_process_text.return_value = "✅ Found 2 tasks for today in your Notion workspace."

        resp = await assistant_service.process_text_message(
            conversation_id=self.conv.id,
            user_id="andrei-main",
            content="What are my tasks today?"
        )

        self.assertEqual(resp.status_code if hasattr(resp, "status_code") else resp.status, "completed")
        self.assertIn("Found 2 tasks", resp.content)

        # Verify messages stored in SQLite
        detail = conversation_service.get_conversation_detail("andrei-main", self.conv.id)
        self.assertEqual(len(detail.messages), 2)
        self.assertEqual(detail.messages[0].role, "user")
        self.assertEqual(detail.messages[0].content, "What are my tasks today?")
        self.assertEqual(detail.messages[1].role, "assistant")
        self.assertIn("Found 2 tasks", detail.messages[1].content)

    @patch.object(gemini_agent, "process_text_message")
    async def test_gemini_error_sanitization(self, mock_process_text):
        """When Gemini throws an exception, client receives safe message without secrets or stack trace."""
        mock_process_text.side_effect = RuntimeError(
            "CRITICAL_GEMINI_FAILURE: QuotaExceeded for key AIzaSyDUMMY_SECRET_KEY_123456"
        )

        resp = await assistant_service.process_text_message(
            conversation_id=self.conv.id,
            user_id="andrei-main",
            content="Check my calendar"
        )

        self.assertEqual(resp.status, "failed")
        # Ensure sensitive token and internal traceback are NEVER in user-facing message
        self.assertNotIn("AIzaSyDUMMY_SECRET_KEY_123456", resp.content)
        self.assertNotIn("CRITICAL_GEMINI_FAILURE", resp.content)
        self.assertIn("encountered an issue", resp.content)

    @patch.object(gemini_agent, "process_voice_message")
    async def test_voice_message_processing(self, mock_process_voice):
        """Voice note audio bytes are passed to agent and result saved."""
        mock_process_voice.return_value = "Task created: Finish report by 5 PM"

        fake_audio = b"OGG_CONTAINER_AUDIO_BYTES_TEST"
        resp = await assistant_service.process_voice_message(
            conversation_id=self.conv.id,
            user_id="andrei-main",
            audio_bytes=fake_audio,
            mime_type="audio/ogg"
        )

        self.assertEqual(resp.status, "completed")
        self.assertIn("Task created", resp.content)
        mock_process_voice.assert_called_once()

    def test_rehydrate_gemini_history_from_sqlite(self):
        """Recent messages in SQLite are rehydrated into Gemini history for coherence."""
        # Insert 3 conversation turns
        for i in range(3):
            conversation_service.save_message(self.conv.id, "andrei-main", "user", f"User question {i}")
            conversation_service.save_message(self.conv.id, "andrei-main", "assistant", f"Assistant answer {i}")

        # Clear in-memory history
        gemini_agent.histories.pop(self.conv.id, None)

        # Call rehydration
        assistant_service._rehydrate_gemini_history(self.conv.id)

        self.assertIn(self.conv.id, gemini_agent.histories)
        rehydrated = gemini_agent.histories[self.conv.id]
        self.assertEqual(len(rehydrated), 6)

if __name__ == "__main__":
    unittest.main()
