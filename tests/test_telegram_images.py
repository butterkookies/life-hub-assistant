import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import telegram_bot
from image_models import (
    AttachmentResult,
    ImageAnalysis,
    PendingImageScan,
    TreadmillScan,
    WorkoutUpsertResult,
)


def treadmill_analysis(confidence=0.97, uncertain_fields=None):
    return ImageAnalysis(
        domain="treadmill",
        summary="TRAX treadmill display",
        confidence=confidence,
        uncertain_fields=uncertain_fields or [],
        treadmill=TreadmillScan(
            date="2026-08-29",
            duration_minutes=40.52,
            distance_km=2.91,
            steps=4006,
            calories_kcal=203,
            confidence=confidence,
            uncertain_fields=uncertain_fields or [],
        ),
    )


class TelegramImageHandlerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        telegram_bot.PENDING_IMAGE_SCANS.clear()
        telegram_bot.RECENT_IMAGE_FILE_IDS.clear()
        telegram_bot.FAILED_IMAGE_ATTACHMENTS.clear()
        self.media = SimpleNamespace(
            file_id="download-id",
            file_unique_id="unique-id",
            file_size=1024,
        )
        self.message = SimpleNamespace(
            photo=[self.media],
            document=None,
            caption="",
            date=datetime(2026, 8, 29, tzinfo=timezone.utc),
            reply_text=AsyncMock(),
        )
        self.update = SimpleNamespace(
            effective_user=SimpleNamespace(id=7),
            effective_chat=SimpleNamespace(id=8),
            message=self.message,
            callback_query=None,
        )
        downloaded = SimpleNamespace(download_to_memory=AsyncMock())
        downloaded.download_to_memory.side_effect = lambda buffer: buffer.write(b"image")
        self.context = SimpleNamespace(
            bot=SimpleNamespace(
                get_file=AsyncMock(return_value=downloaded),
                send_chat_action=AsyncMock(),
            )
        )

    @patch("telegram_bot.settings.is_authorized", return_value=False)
    async def test_unauthorized_image_is_rejected_before_download(self, _authorized):
        await telegram_bot.handle_image(self.update, self.context)

        self.context.bot.get_file.assert_not_awaited()
        self.message.reply_text.assert_awaited()

    @patch("telegram_bot.notion_service.attach_image")
    @patch("telegram_bot.notion_service.upsert_daily_workout")
    @patch("telegram_bot.gemini_agent.process_image_message")
    @patch("telegram_bot.settings.is_authorized", return_value=True)
    async def test_valid_scan_auto_saves_and_attaches(
        self, _authorized, analyze, upsert, attach
    ):
        analyze.return_value = treadmill_analysis()
        upsert.return_value = WorkoutUpsertResult(
            action="created",
            page_id="page-id",
            page_url="https://notion.test/page",
            written_fields=["duration_minutes", "distance_km"],
        )
        attach.return_value = AttachmentResult(attached=True, file_upload_id="upload")

        await telegram_bot.handle_image(self.update, self.context)

        upsert.assert_called_once()
        attach.assert_called_once()
        self.assertIn("unique-id", telegram_bot.RECENT_IMAGE_FILE_IDS)
        reply = self.message.reply_text.await_args.args[0]
        self.assertIn("Workout saved", reply)

    @patch("telegram_bot.notion_service.upsert_daily_workout")
    @patch("telegram_bot.gemini_agent.process_image_message")
    @patch("telegram_bot.settings.is_authorized", return_value=True)
    async def test_uncertain_scan_creates_preview_without_notion_write(
        self, _authorized, analyze, upsert
    ):
        analyze.return_value = treadmill_analysis(0.75, ["distance_km"])

        await telegram_bot.handle_image(self.update, self.context)

        upsert.assert_not_called()
        self.assertEqual(len(telegram_bot.PENDING_IMAGE_SCANS), 1)
        kwargs = self.message.reply_text.await_args.kwargs
        self.assertIsNotNone(kwargs["reply_markup"])

    @patch("telegram_bot.notion_service.upsert_daily_workout")
    @patch("telegram_bot.gemini_agent.process_image_message")
    @patch("telegram_bot.settings.is_authorized", return_value=True)
    async def test_other_image_never_writes_to_notion(
        self, _authorized, analyze, upsert
    ):
        analyze.return_value = ImageAnalysis(
            domain="other", summary="A handwritten class note", confidence=0.95
        )

        await telegram_bot.handle_image(self.update, self.context)

        upsert.assert_not_called()
        reply = self.message.reply_text.await_args.args[0]
        self.assertIn("handwritten class note", reply)

    @patch("telegram_bot.gemini_agent.process_image_message")
    @patch("telegram_bot.settings.is_authorized", return_value=True)
    async def test_unsupported_or_oversized_image_never_reaches_gemini(
        self, _authorized, analyze
    ):
        self.message.photo = []
        self.message.document = SimpleNamespace(
            file_id="doc",
            file_unique_id="doc-unique",
            file_size=telegram_bot.MAX_IMAGE_BYTES + 1,
            file_name="display.gif",
            mime_type="image/gif",
        )

        await telegram_bot.handle_image(self.update, self.context)

        analyze.assert_not_called()
        self.context.bot.get_file.assert_not_awaited()

    @patch("telegram_bot.notion_service.attach_image")
    @patch("telegram_bot.notion_service.upsert_daily_workout")
    @patch("telegram_bot.gemini_agent.process_image_message")
    @patch("telegram_bot.settings.is_authorized", return_value=True)
    async def test_attachment_failure_keeps_saved_metrics_and_warns(
        self, _authorized, analyze, upsert, attach
    ):
        analyze.return_value = treadmill_analysis()
        upsert.return_value = WorkoutUpsertResult(
            action="updated", page_id="page-id", written_fields=["distance_km"]
        )
        attach.return_value = AttachmentResult(attached=False, error="temporary")

        await telegram_bot.handle_image(self.update, self.context)

        upsert.assert_called_once()
        reply = self.message.reply_text.await_args.args[0]
        self.assertIn("upload failed", reply)
        self.assertNotIn("unique-id", telegram_bot.RECENT_IMAGE_FILE_IDS)
        self.assertIn("unique-id", telegram_bot.FAILED_IMAGE_ATTACHMENTS)

    @patch("telegram_bot.notion_service.attach_image")
    @patch("telegram_bot.notion_service.upsert_daily_workout")
    @patch("telegram_bot.gemini_agent.process_image_message")
    @patch("telegram_bot.settings.is_authorized", return_value=True)
    async def test_resend_after_attachment_failure_retries_only_attachment(
        self, _authorized, analyze, upsert, attach
    ):
        telegram_bot.FAILED_IMAGE_ATTACHMENTS["unique-id"] = (
            "page-id",
            "https://notion.test/page",
            datetime.now(timezone.utc),
        )
        attach.return_value = AttachmentResult(
            attached=True, file_upload_id="upload-id"
        )

        await telegram_bot.handle_image(self.update, self.context)

        attach.assert_called_once()
        analyze.assert_not_called()
        upsert.assert_not_called()
        self.assertNotIn("unique-id", telegram_bot.FAILED_IMAGE_ATTACHMENTS)
        self.assertIn("unique-id", telegram_bot.RECENT_IMAGE_FILE_IDS)

    @patch("telegram_bot.notion_service.attach_image")
    @patch("telegram_bot.gemini_agent.process_image_message")
    @patch("telegram_bot.settings.is_authorized", return_value=True)
    async def test_indeterminate_retry_is_not_queued_again(
        self, _authorized, analyze, attach
    ):
        telegram_bot.FAILED_IMAGE_ATTACHMENTS["unique-id"] = (
            "page-id",
            "https://notion.test/page",
            datetime.now(timezone.utc),
        )
        attach.return_value = AttachmentResult(
            attached=False,
            retryable=False,
            file_upload_id="upload-id",
            error="timeout",
        )

        await telegram_bot.handle_image(self.update, self.context)

        analyze.assert_not_called()
        self.assertNotIn("unique-id", telegram_bot.FAILED_IMAGE_ATTACHMENTS)
        reply = self.message.reply_text.await_args.args[0]
        self.assertIn("avoid a duplicate", reply)

    async def test_invalid_scan_preview_has_no_save_button(self):
        invalid = treadmill_analysis(0.75)
        invalid.treadmill.duration_minutes = 1
        invalid.treadmill.distance_km = 5
        pending = telegram_bot._new_pending_scan(
            self.update,
            invalid,
            b"image",
            "image/jpeg",
            "scan.jpg",
            "invalid-id",
        )

        await telegram_bot._send_scan_preview(self.message, pending)

        keyboard = self.message.reply_text.await_args.kwargs["reply_markup"]
        callbacks = [button.callback_data for button in keyboard.inline_keyboard[0]]
        self.assertFalse(any(data.startswith("scan:save:") for data in callbacks))

    async def test_pending_correction_is_bound_to_chat(self):
        pending = PendingImageScan(
            token="token",
            user_id=7,
            chat_id=8,
            image_bytes=b"image",
            mime_type="image/jpeg",
            filename="scan.jpg",
            analysis=treadmill_analysis(0.75),
            awaiting_correction=True,
        )
        telegram_bot.PENDING_IMAGE_SCANS[pending.token] = pending

        self.assertIsNone(telegram_bot._pending_correction_for_user(7, 999))
        self.assertIs(telegram_bot._pending_correction_for_user(7, 8), pending)

    async def test_new_pending_scan_replaces_same_user_chat_state(self):
        first = telegram_bot._new_pending_scan(
            self.update,
            treadmill_analysis(0.75),
            b"first",
            "image/jpeg",
            "first.jpg",
            "first-id",
        )
        second = telegram_bot._new_pending_scan(
            self.update,
            treadmill_analysis(0.75),
            b"second",
            "image/jpeg",
            "second.jpg",
            "second-id",
        )

        self.assertNotIn(first.token, telegram_bot.PENDING_IMAGE_SCANS)
        self.assertIn(second.token, telegram_bot.PENDING_IMAGE_SCANS)

    @patch("telegram_bot.notion_service.attach_image")
    @patch("telegram_bot.notion_service.upsert_daily_workout")
    @patch("telegram_bot.settings.is_authorized", return_value=True)
    async def test_first_save_that_finds_conflicts_requires_second_confirmation(
        self, _authorized, upsert, attach
    ):
        pending = PendingImageScan(
            token="token",
            user_id=7,
            chat_id=8,
            image_bytes=b"image",
            mime_type="image/jpeg",
            filename="scan.jpg",
            analysis=treadmill_analysis(0.75),
        )
        telegram_bot.PENDING_IMAGE_SCANS[pending.token] = pending
        upsert.return_value = WorkoutUpsertResult(
            action="conflict",
            page_id="page-id",
            conflicts={"distance_km": (0.86, 2.91)},
        )
        query = SimpleNamespace(
            data="scan:save:token",
            from_user=SimpleNamespace(id=7),
            message=SimpleNamespace(chat_id=8),
            answer=AsyncMock(),
            edit_message_text=AsyncMock(),
        )
        update = SimpleNamespace(
            effective_user=query.from_user,
            effective_chat=SimpleNamespace(id=8),
            message=None,
            callback_query=query,
        )

        await telegram_bot.handle_scan_callback(update, self.context)

        self.assertFalse(upsert.call_args.kwargs["allow_overwrite"])
        attach.assert_not_called()
        self.assertEqual(
            telegram_bot.PENDING_IMAGE_SCANS["token"].shown_conflicts,
            {"distance_km": (0.86, 2.91)},
        )
        self.assertIn("Existing values differ", query.edit_message_text.await_args.args[0])

    @patch("telegram_bot.notion_service.attach_image")
    @patch("telegram_bot.notion_service.upsert_daily_workout")
    @patch("telegram_bot.settings.is_authorized", return_value=True)
    async def test_save_callback_is_bound_to_pending_user(
        self, _authorized, upsert, attach
    ):
        pending = PendingImageScan(
            token="token",
            user_id=7,
            chat_id=8,
            image_bytes=b"image",
            mime_type="image/jpeg",
            filename="scan.jpg",
            analysis=treadmill_analysis(0.75, ["distance_km"]),
        )
        telegram_bot.PENDING_IMAGE_SCANS[pending.token] = pending
        query = SimpleNamespace(
            data="scan:save:token",
            from_user=SimpleNamespace(id=99),
            message=SimpleNamespace(chat_id=8),
            answer=AsyncMock(),
            edit_message_text=AsyncMock(),
        )
        update = SimpleNamespace(
            effective_user=query.from_user,
            effective_chat=SimpleNamespace(id=8),
            message=None,
            callback_query=query,
        )

        await telegram_bot.handle_scan_callback(update, self.context)

        upsert.assert_not_called()
        attach.assert_not_called()
        query.answer.assert_awaited()
        self.assertIn("not yours", query.answer.await_args.args[0].lower())


if __name__ == "__main__":
    unittest.main()
