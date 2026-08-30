import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from image_models import ImageAnalysis, PendingImageScan, TreadmillScan


class TreadmillScanTests(unittest.TestCase):
    def test_complete_plausible_scan_is_auto_save_eligible(self):
        scan = TreadmillScan(
            date="2026-08-29",
            duration_minutes=40.52,
            distance_km=2.91,
            steps=4006,
            calories_kcal=203,
            speed_kmh=2.4,
            workout_type="🚶 Walking",
            confidence=0.97,
        )

        self.assertEqual(scan.validation_errors(), [])
        self.assertTrue(scan.is_auto_save_eligible())

    def test_low_confidence_and_uncertain_fields_require_confirmation(self):
        scan = TreadmillScan(
            date="2026-08-29",
            duration_minutes=15,
            distance_km=0.86,
            confidence=0.82,
            uncertain_fields=["distance_km"],
        )

        self.assertFalse(scan.is_auto_save_eligible())

    def test_duration_and_one_core_metric_are_required(self):
        no_duration = TreadmillScan(
            date="2026-08-29", distance_km=2.91, confidence=0.99
        )
        no_metric = TreadmillScan(
            date="2026-08-29", duration_minutes=40, confidence=0.99
        )

        self.assertIn("duration_minutes is required", no_duration.validation_errors())
        self.assertIn(
            "at least one core workout metric is required",
            no_metric.validation_errors(),
        )

    def test_out_of_range_values_are_reported(self):
        scan = TreadmillScan(
            date="2026-08-29",
            duration_minutes=601,
            distance_km=101,
            steps=200001,
            calories_kcal=5001,
            speed_kmh=31,
            heart_rate_bpm=241,
            confidence=0.99,
        )

        self.assertEqual(len(scan.validation_errors()), 6)

    def test_impossible_distance_for_duration_is_reported(self):
        scan = TreadmillScan(
            date="2026-08-29",
            duration_minutes=1,
            distance_km=5,
            confidence=0.99,
        )

        self.assertIn(
            "distance is impossible for the recorded duration",
            scan.validation_errors(),
        )

    def test_image_analysis_requires_scan_only_for_treadmill_domain(self):
        with self.assertRaises(ValidationError):
            ImageAnalysis(domain="treadmill", summary="display", confidence=0.9)

        other = ImageAnalysis(domain="other", summary="A handwritten note", confidence=0.8)
        self.assertIsNone(other.treadmill)

    def test_pending_scan_expiration(self):
        pending = PendingImageScan(
            token="opaque",
            user_id=7,
            chat_id=8,
            created_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
            image_bytes=b"image",
            mime_type="image/jpeg",
            filename="scan.jpg",
            analysis=ImageAnalysis(
                domain="treadmill",
                summary="Treadmill",
                confidence=0.8,
                treadmill=TreadmillScan(
                    date="2026-08-29",
                    duration_minutes=10,
                    distance_km=1,
                    confidence=0.8,
                ),
            ),
        )

        self.assertFalse(
            pending.is_expired(datetime(2026, 8, 29, 0, 9, tzinfo=timezone.utc))
        )
        self.assertTrue(
            pending.is_expired(datetime(2026, 8, 29, 0, 11, tzinfo=timezone.utc))
        )


if __name__ == "__main__":
    unittest.main()
