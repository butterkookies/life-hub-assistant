"""Private attachment storage backed by local disk or Cloudflare R2."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config import settings
from server.database import get_upload_dir

logger = logging.getLogger("server.storage")


class ObjectStorage:
    def __init__(self) -> None:
        self._client = None
        self._client_config: Optional[tuple[str, str, str]] = None

    def is_remote(self) -> bool:
        return bool(
            settings.R2_ENDPOINT_URL
            and settings.R2_ACCESS_KEY_ID
            and settings.R2_SECRET_ACCESS_KEY
            and settings.R2_BUCKET
        )

    def _r2_client(self):
        config = (
            settings.R2_ENDPOINT_URL,
            settings.R2_ACCESS_KEY_ID,
            settings.R2_SECRET_ACCESS_KEY,
        )
        if self._client is None or self._client_config != config:
            import boto3
            from botocore.config import Config

            self._client = boto3.client(
                "s3",
                endpoint_url=config[0],
                aws_access_key_id=config[1],
                aws_secret_access_key=config[2],
                region_name="auto",
                config=Config(signature_version="s3v4"),
            )
            self._client_config = config
        return self._client

    def validate(self) -> None:
        if self.is_remote():
            self._r2_client().head_bucket(Bucket=settings.R2_BUCKET)
            return
        Path(get_upload_dir()).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def attachment_key(user_id: str, attachment_id: str, filename: str) -> str:
        safe_name = Path(filename).name
        return f"attachments/{user_id}/{attachment_id}/{safe_name}"

    @staticmethod
    def pending_scan_key(user_id: str, token: str, filename: str) -> str:
        safe_name = Path(filename).name
        return f"pending-scans/{user_id}/{token}/{safe_name}"

    def put_bytes(self, key: str, content: bytes, content_type: str) -> None:
        if self.is_remote():
            self._r2_client().put_object(
                Bucket=settings.R2_BUCKET,
                Key=key,
                Body=content,
                ContentType=content_type,
            )
            return
        path = self._local_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def get_bytes(self, key: str) -> bytes:
        if self.is_remote():
            response = self._r2_client().get_object(Bucket=settings.R2_BUCKET, Key=key)
            return response["Body"].read()
        return self._local_path(key).read_bytes()

    def delete(self, key: str) -> None:
        if not key:
            return
        if self.is_remote():
            self._r2_client().delete_object(Bucket=settings.R2_BUCKET, Key=key)
            return
        path = self._local_path(key)
        if path.exists():
            path.unlink()

    def delete_quietly(self, key: str) -> bool:
        try:
            self.delete(key)
            return True
        except Exception as exc:
            logger.warning("Could not remove stored object %s: %s", key, exc)
            self._queue_cleanup(key, exc)
            return False

    def _queue_cleanup(self, key: str, error: Exception) -> None:
        """Persist failed deletes so later process starts can retry them."""
        try:
            from server.database import get_db

            with get_db() as db:
                db.execute(
                    """
                    INSERT INTO object_cleanup_queue (object_key, attempts, last_error, updated_at)
                    VALUES (?, 1, ?, ?)
                    ON CONFLICT(object_key) DO UPDATE SET
                        attempts = object_cleanup_queue.attempts + 1,
                        last_error = excluded.last_error,
                        updated_at = excluded.updated_at
                    """,
                    (key, str(error)[:500], datetime.now(timezone.utc).isoformat()),
                )
        except Exception as queue_error:
            logger.error("Could not queue object cleanup for %s: %s", key, queue_error)

    def retry_pending_deletes(self, limit: int = 100) -> int:
        """Retry queued object deletions and remove successful queue records."""
        from server.database import get_db

        with get_db() as db:
            rows = db.execute(
                "SELECT object_key FROM object_cleanup_queue ORDER BY updated_at ASC LIMIT ?",
                (limit,),
            ).fetchall()

        completed = 0
        for row in rows:
            key = str(row["object_key"])
            try:
                self.delete(key)
                with get_db() as db:
                    db.execute("DELETE FROM object_cleanup_queue WHERE object_key = ?", (key,))
                completed += 1
            except Exception as exc:
                logger.warning("Queued object cleanup still failing for %s: %s", key, exc)
                self._queue_cleanup(key, exc)
        return completed

    def _local_path(self, key: str) -> Path:
        candidate = Path(key)
        root = Path(get_upload_dir()).resolve()
        resolved = candidate.resolve() if candidate.is_absolute() else (root / candidate).resolve()
        if root != resolved and root not in resolved.parents:
            raise ValueError("Invalid storage key")
        return resolved


object_storage = ObjectStorage()
