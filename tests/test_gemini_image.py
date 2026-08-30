import json
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from gemini_agent import GeminiNotionAgent, MODEL_TIERS


class GeminiImageAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.agent = GeminiNotionAgent()
        self.agent.client = MagicMock()
        self.valid_payload = {
            "domain": "treadmill",
            "summary": "TRAX treadmill workout display",
            "confidence": 0.97,
            "uncertain_fields": [],
            "treadmill": {
                "date": "2026-08-29",
                "duration_minutes": 40.52,
                "distance_km": 2.91,
                "steps": 4006,
                "calories_kcal": 203,
                "speed_kmh": 2.4,
                "confidence": 0.97,
            },
        }

    def test_image_analysis_uses_inline_bytes_and_structured_schema(self):
        self.agent.client.models.generate_content.return_value = SimpleNamespace(
            text=json.dumps(self.valid_payload)
        )

        result = self.agent.process_image_message(
            "7",
            b"jpeg-bytes",
            "image/jpeg",
            "Log this workout",
            datetime(2026, 8, 29, 1, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(result.domain, "treadmill")
        self.assertEqual(result.treadmill.workout_type, "🚶 Walking")
        call = self.agent.client.models.generate_content.call_args
        self.assertEqual(call.kwargs["model"], MODEL_TIERS[0]["model"])
        self.assertEqual(call.kwargs["contents"][0].inline_data.data, b"jpeg-bytes")
        config = call.kwargs["config"]
        self.assertEqual(config.response_mime_type, "application/json")
        self.assertIsNotNone(config.response_json_schema)
        prompt = call.kwargs["contents"][1]
        self.assertIn("untrusted data", prompt)
        self.assertIn("2026-08-29", prompt)

    def test_image_analysis_falls_back_to_next_stable_model(self):
        self.agent.client.models.generate_content.side_effect = [
            RuntimeError("rate limited"),
            SimpleNamespace(text=json.dumps(self.valid_payload)),
        ]

        result = self.agent.process_image_message(
            "7",
            b"image",
            "image/png",
            "",
            datetime(2026, 8, 29, tzinfo=timezone.utc),
        )

        self.assertEqual(result.domain, "treadmill")
        attempted = [
            call.kwargs["model"]
            for call in self.agent.client.models.generate_content.call_args_list
        ]
        self.assertEqual(attempted[:2], [tier["model"] for tier in MODEL_TIERS[:2]])
        self.assertNotIn("gemini-3.1-flash-lite-preview", attempted)

    def test_correction_revalidates_original_scan_as_structured_output(self):
        corrected = dict(self.valid_payload)
        corrected["treadmill"] = dict(self.valid_payload["treadmill"])
        corrected["treadmill"]["distance_km"] = 3.01
        self.agent.client.models.generate_content.return_value = SimpleNamespace(
            text=json.dumps(corrected)
        )
        original = self.agent.process_image_message(
            "7",
            b"image",
            "image/png",
            "",
            datetime(2026, 8, 29, tzinfo=timezone.utc),
        )
        self.agent.client.models.generate_content.reset_mock()
        self.agent.client.models.generate_content.return_value = SimpleNamespace(
            text=json.dumps(corrected)
        )

        result = self.agent.apply_image_correction(original, "Distance is 3.01 km")

        self.assertEqual(result.treadmill.distance_km, 3.01)
        prompt = self.agent.client.models.generate_content.call_args.kwargs["contents"]
        self.assertIn("Distance is 3.01 km", prompt)


if __name__ == "__main__":
    unittest.main()
