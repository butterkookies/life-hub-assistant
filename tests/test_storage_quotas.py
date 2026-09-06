"""Application-enforced R2 safety limits."""

import io
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from server.database import close_db, init_db
from server.storage import StorageQuotaExceeded, object_storage


class StorageQuotaTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.db_path = os.path.join(self.temp_dir.name, "quota.db")
        self.env_patch = patch.dict(
            os.environ,
            {
                "DATABASE_URL": "",
                "DATABASE_PATH": self.db_path,
                "UPLOAD_DIR": os.path.join(self.temp_dir.name, "uploads"),
                "R2_ENDPOINT_URL": "https://test.r2.cloudflarestorage.com",
                "R2_ACCESS_KEY_ID": "test-access",
                "R2_SECRET_ACCESS_KEY": "test-secret",
                "R2_BUCKET": "test-bucket",
                "R2_MAX_STORAGE_BYTES": "5",
                "R2_MAX_WRITES_31D": "10",
                "R2_MAX_READS_31D": "10",
            },
        )
        self.env_patch.start()
        init_db()
        self.client = MagicMock()
        object_storage._client = self.client
        object_storage._client_config = (
            "https://test.r2.cloudflarestorage.com",
            "test-access",
            "test-secret",
        )

    def tearDown(self):
        object_storage._client = None
        object_storage._client_config = None
        close_db()
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def test_storage_limit_blocks_upload_before_r2_call(self):
        object_storage.put_bytes("first", b"1234", "text/plain")

        with self.assertRaises(StorageQuotaExceeded):
            object_storage.put_bytes("second", b"12", "text/plain")

        self.assertEqual(self.client.put_object.call_count, 1)
        self.assertEqual(object_storage.quota_snapshot()["storage_bytes"], 4)

    def test_rolling_write_limit_blocks_extra_upload(self):
        os.environ["R2_MAX_STORAGE_BYTES"] = "100"
        os.environ["R2_MAX_WRITES_31D"] = "1"
        object_storage.put_bytes("first", b"1", "text/plain")

        with self.assertRaises(StorageQuotaExceeded):
            object_storage.put_bytes("second", b"2", "text/plain")

        self.assertEqual(self.client.put_object.call_count, 1)
        self.assertEqual(object_storage.quota_snapshot()["writes_31d"], 1)

    def test_rolling_read_limit_blocks_extra_download(self):
        os.environ["R2_MAX_READS_31D"] = "1"
        self.client.get_object.side_effect = lambda **_: {"Body": io.BytesIO(b"stored")}

        self.assertEqual(object_storage.get_bytes("first"), b"stored")
        with self.assertRaises(StorageQuotaExceeded):
            object_storage.get_bytes("first")

        self.assertEqual(self.client.get_object.call_count, 1)
        self.assertEqual(object_storage.quota_snapshot()["reads_31d"], 1)


if __name__ == "__main__":
    unittest.main()
