import unittest
from unittest.mock import MagicMock

from image_models import TreadmillScan
from notion_service import NotionService


def notion_property(prop_type, value):
    return {"type": prop_type, prop_type: value}


class NotionWorkoutTests(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.service = NotionService(api_key="test")
        self.service.client = self.client
        self.scan = TreadmillScan(
            date="2026-08-29",
            duration_minutes=40.52,
            distance_km=2.91,
            steps=4006,
            calories_kcal=203,
            speed_kmh=2.4,
            workout_type="🚶 Walking",
            confidence=0.97,
        )

    def test_creates_daily_row_with_exact_property_mapping(self):
        self.client.data_sources.query.return_value = {"results": []}
        self.client.pages.create.return_value = {
            "id": "new-page",
            "url": "https://notion.test/new-page",
        }

        result = self.service.upsert_daily_workout(self.scan)

        self.assertEqual(result.action, "created")
        body = self.client.pages.create.call_args.kwargs
        self.assertEqual(
            body["parent"], {"data_source_id": self.service.HEALTH_LOG_DATA_SOURCE_ID}
        )
        self.assertEqual(body["properties"]["Duration (min)"]["number"], 40.52)
        self.assertEqual(body["properties"]["Treadmill Steps"]["number"], 4006)
        self.assertEqual(
            body["properties"]["Workout Type"]["select"]["name"], "🚶 Walking"
        )

    def test_rejects_deterministically_invalid_scan_before_query(self):
        invalid = TreadmillScan(
            date="2026-08-29",
            duration_minutes=1,
            distance_km=5,
            confidence=0.99,
        )

        with self.assertRaises(ValueError):
            self.service.upsert_daily_workout(invalid)

        self.client.data_sources.query.assert_not_called()

    def test_fills_only_missing_workout_fields(self):
        self.client.data_sources.query.return_value = {
            "results": [
                {
                    "id": "existing",
                    "url": "https://notion.test/existing",
                    "properties": {
                        "Duration (min)": notion_property("number", None),
                        "Distance (km)": notion_property("number", 2.91),
                        "Sleep (hrs)": notion_property("number", 8),
                    },
                }
            ]
        }
        self.client.pages.update.return_value = {
            "id": "existing",
            "url": "https://notion.test/existing",
        }

        result = self.service.upsert_daily_workout(self.scan)

        self.assertEqual(result.action, "updated")
        props = self.client.pages.update.call_args.kwargs["properties"]
        self.assertEqual(props["Duration (min)"]["number"], 40.52)
        self.assertNotIn("Distance (km)", props)
        self.assertNotIn("Sleep (hrs)", props)

    def test_conflicts_require_confirmation_without_mutation(self):
        self.client.data_sources.query.return_value = {
            "results": [
                {
                    "id": "existing",
                    "url": "https://notion.test/existing",
                    "properties": {
                        "Duration (min)": notion_property("number", 15),
                        "Distance (km)": notion_property("number", 0.86),
                    },
                }
            ]
        }

        result = self.service.upsert_daily_workout(self.scan)

        self.assertEqual(result.action, "conflict")
        self.assertEqual(result.conflicts["duration_minutes"], (15, 40.52))
        self.client.pages.update.assert_not_called()

    def test_confirmed_conflicts_replace_only_workout_fields(self):
        self.client.data_sources.query.return_value = {
            "results": [
                {
                    "id": "existing",
                    "url": "https://notion.test/existing",
                    "properties": {
                        "Duration (min)": notion_property("number", 15),
                        "Sleep (hrs)": notion_property("number", 8),
                    },
                }
            ]
        }
        self.client.pages.update.return_value = {
            "id": "existing",
            "url": "https://notion.test/existing",
        }

        result = self.service.upsert_daily_workout(
            self.scan,
            allow_overwrite=True,
            expected_conflicts={"duration_minutes": (15, 40.52)},
        )

        self.assertEqual(result.action, "updated")
        props = self.client.pages.update.call_args.kwargs["properties"]
        self.assertEqual(props["Duration (min)"]["number"], 40.52)
        self.assertNotIn("Sleep (hrs)", props)

    def test_overwrite_without_confirmed_snapshot_fails_closed(self):
        self.client.data_sources.query.return_value = {
            "results": [
                {
                    "id": "existing",
                    "properties": {
                        "Duration (min)": notion_property("number", 15),
                    },
                }
            ]
        }

        result = self.service.upsert_daily_workout(
            self.scan, allow_overwrite=True
        )

        self.assertEqual(result.action, "conflict")
        self.client.pages.update.assert_not_called()

    def test_overwrite_rechecks_the_exact_confirmed_conflict_snapshot(self):
        self.client.data_sources.query.return_value = {
            "results": [
                {
                    "id": "existing",
                    "properties": {
                        "Duration (min)": notion_property("number", 20),
                    },
                }
            ]
        }

        result = self.service.upsert_daily_workout(
            self.scan,
            allow_overwrite=True,
            expected_conflicts={"duration_minutes": (15, 40.52)},
        )

        self.assertEqual(result.action, "conflict")
        self.assertEqual(result.conflicts["duration_minutes"], (20, 40.52))
        self.client.pages.update.assert_not_called()

    def test_exact_match_is_duplicate_and_does_not_mutate(self):
        self.client.data_sources.query.return_value = {
            "results": [
                {
                    "id": "existing",
                    "url": "https://notion.test/existing",
                    "properties": {
                        "Duration (min)": notion_property("number", 40.52),
                        "Distance (km)": notion_property("number", 2.91),
                        "Treadmill Steps": notion_property("number", 4006),
                        "Workout Calories": notion_property("number", 203),
                        "Speed (km/h)": notion_property("number", 2.4),
                        "Workout Type": notion_property(
                            "select", {"name": "🚶 Walking"}
                        ),
                    },
                }
            ]
        }

        result = self.service.upsert_daily_workout(self.scan)

        self.assertEqual(result.action, "duplicate")
        self.client.pages.update.assert_not_called()

    def test_attach_image_uploads_and_appends_image_block(self):
        self.client.file_uploads.create.return_value = {"id": "upload-id"}
        self.client.file_uploads.send.return_value = {"status": "uploaded"}
        self.client.blocks.children.append.return_value = {"results": []}

        result = self.service.attach_image(
            "page-id", b"image", "image/jpeg", "treadmill.jpg"
        )

        self.assertTrue(result.attached)
        sent_file = self.client.file_uploads.send.call_args.kwargs["file"]
        self.assertEqual(sent_file[0], "treadmill.jpg")
        self.assertEqual(sent_file[1], b"image")
        children = self.client.blocks.children.append.call_args.kwargs["children"]
        self.assertEqual(children[0]["image"]["file_upload"]["id"], "upload-id")

    def test_failed_upload_never_appends_an_incomplete_file(self):
        self.client.file_uploads.create.return_value = {"id": "upload-id"}
        self.client.file_uploads.send.side_effect = RuntimeError("temporary")

        result = self.service.attach_image(
            "page-id", b"image", "image/jpeg", "scan.jpg"
        )

        self.assertFalse(result.attached)
        self.assertEqual(self.client.file_uploads.send.call_count, 3)
        self.client.blocks.children.append.assert_not_called()

    def test_ambiguous_append_failure_is_not_automatically_retryable(self):
        self.client.file_uploads.create.return_value = {"id": "upload-id"}
        self.client.file_uploads.send.return_value = {"status": "uploaded"}
        self.client.blocks.children.append.side_effect = TimeoutError("unknown")

        result = self.service.attach_image(
            "page-id", b"image", "image/jpeg", "scan.jpg"
        )

        self.assertFalse(result.attached)
        self.assertFalse(result.retryable)
        self.assertEqual(result.file_upload_id, "upload-id")
        self.client.blocks.children.append.assert_called_once()


if __name__ == "__main__":
    unittest.main()
