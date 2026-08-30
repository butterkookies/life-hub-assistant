"""Typed contracts for Telegram image analysis and workout persistence."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TreadmillScan(BaseModel):
    """Structured values observed on a treadmill display."""

    date: str
    duration_minutes: Optional[float] = None
    distance_km: Optional[float] = None
    steps: Optional[int] = None
    calories_kcal: Optional[float] = None
    speed_kmh: Optional[float] = None
    heart_rate_bpm: Optional[int] = None
    trax_program: Optional[str] = None
    workout_type: str = "🚶 Walking"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    uncertain_fields: list[str] = Field(default_factory=list)
    raw_text: str = ""

    @model_validator(mode="after")
    def validate_date_format(self) -> "TreadmillScan":
        date.fromisoformat(self.date)
        return self

    def validation_errors(self) -> list[str]:
        """Return deterministic plausibility failures without mutating the scan."""
        errors: list[str] = []
        ranges = {
            "duration_minutes": (self.duration_minutes, 0.1, 600),
            "distance_km": (self.distance_km, 0, 100),
            "steps": (self.steps, 0, 200_000),
            "calories_kcal": (self.calories_kcal, 0, 5_000),
            "speed_kmh": (self.speed_kmh, 0, 30),
            "heart_rate_bpm": (self.heart_rate_bpm, 30, 240),
        }
        for name, (value, minimum, maximum) in ranges.items():
            if value is not None and not minimum <= value <= maximum:
                errors.append(f"{name} is outside the allowed range")

        if self.duration_minutes is None:
            errors.append("duration_minutes is required")

        core_metrics = (
            self.distance_km,
            self.steps,
            self.calories_kcal,
            self.speed_kmh,
        )
        if all(value is None for value in core_metrics):
            errors.append("at least one core workout metric is required")

        duration_valid = (
            self.duration_minutes is not None and 0.1 <= self.duration_minutes <= 600
        )
        distance_valid = self.distance_km is not None and 0 <= self.distance_km <= 100
        if duration_valid and distance_valid:
            maximum_possible_distance = (self.duration_minutes / 60) * 30
            if self.distance_km > maximum_possible_distance + 0.05:
                errors.append("distance is impossible for the recorded duration")
        return errors

    def is_auto_save_eligible(self) -> bool:
        return (
            self.confidence >= 0.90
            and not self.uncertain_fields
            and not self.validation_errors()
        )


class ImageAnalysis(BaseModel):
    """Domain routing and structured extraction result for one image."""

    domain: Literal["treadmill", "other"]
    summary: str
    confidence: float = Field(ge=0.0, le=1.0)
    uncertain_fields: list[str] = Field(default_factory=list)
    treadmill: Optional[TreadmillScan] = None

    @model_validator(mode="after")
    def require_domain_payload(self) -> "ImageAnalysis":
        if self.domain == "treadmill" and self.treadmill is None:
            raise ValueError("treadmill analysis requires treadmill values")
        if self.treadmill is not None:
            self.treadmill.confidence = min(
                self.treadmill.confidence, self.confidence
            )
            self.treadmill.uncertain_fields = sorted(
                set(self.treadmill.uncertain_fields + self.uncertain_fields)
            )
        return self


class WorkoutUpsertResult(BaseModel):
    """Outcome of a deterministic daily workout write."""

    action: Literal["created", "updated", "duplicate", "conflict"]
    page_id: str
    page_url: Optional[str] = None
    written_fields: list[str] = Field(default_factory=list)
    conflicts: dict[str, tuple[Any, Any]] = Field(default_factory=dict)


class AttachmentResult(BaseModel):
    attached: bool
    file_upload_id: Optional[str] = None
    error: Optional[str] = None
    retryable: bool = True


class PendingImageScan(BaseModel):
    """Short-lived image state used by Telegram confirmation callbacks."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    token: str
    user_id: int
    chat_id: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    image_bytes: bytes = Field(repr=False)
    mime_type: str
    filename: str
    file_unique_id: Optional[str] = None
    analysis: ImageAnalysis
    awaiting_correction: bool = False
    shown_conflicts: dict[str, tuple[Any, Any]] = Field(default_factory=dict)

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        current = now or datetime.now(timezone.utc)
        return current >= self.created_at + timedelta(minutes=10)
