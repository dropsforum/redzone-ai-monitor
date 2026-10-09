import hashlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_motion_app import model_cache


class ModelCacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.cache = Path(self.temporary.name)
        self.content = b"official checkpoint fixture"
        self.name = "yolo26n-seg.pt"
        self.env = patch.dict(os.environ, {"REDZONE_MODEL_CACHE": str(self.cache)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.hashes = patch.dict(model_cache.MODEL_ASSETS, {self.name: hashlib.sha256(self.content).hexdigest()})
        self.hashes.start()
        self.addCleanup(self.hashes.stop)

    def test_download_verifies_before_atomic_install(self):
        messages = []
        with patch.object(model_cache, "urlopen", return_value=io.BytesIO(self.content)) as request:
            target = model_cache.ensure_model(self.name, messages.append)
        self.assertEqual(self.content, target.read_bytes())
        self.assertEqual(["Downloading AI model"], messages)
        request.assert_called_once_with(model_cache.MODEL_SOURCE + self.name, timeout=30)
        self.assertEqual([self.name], [item.name for item in self.cache.iterdir()])

    def test_valid_cache_is_offline(self):
        (self.cache / self.name).write_bytes(self.content)
        with patch.object(model_cache, "urlopen") as request:
            self.assertEqual(self.cache / self.name, model_cache.ensure_model(self.name))
        request.assert_not_called()

    def test_bad_download_cannot_replace_existing_file(self):
        target = self.cache / self.name
        target.write_bytes(b"old invalid checkpoint")
        with patch.object(model_cache, "urlopen", return_value=io.BytesIO(b"corrupt")):
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                model_cache.ensure_model(self.name)
        self.assertEqual(b"old invalid checkpoint", target.read_bytes())
        self.assertEqual([self.name], [item.name for item in self.cache.iterdir()])

    def test_interrupted_download_leaves_no_partial_file(self):
        with patch.object(model_cache, "urlopen", side_effect=TimeoutError("offline")):
            with self.assertRaises(TimeoutError):
                model_cache.ensure_model(self.name)
        self.assertEqual([], list(self.cache.iterdir()))

    def test_rejects_unconfigured_names_and_path_traversal(self):
        with patch.object(model_cache, "urlopen") as request:
            for name in ["../../private.pt", "unknown.pt"]:
                with self.assertRaises(ValueError):
                    model_cache.ensure_model(name)
        request.assert_not_called()

    def test_oversized_download_is_discarded(self):
        with patch.object(model_cache, "MAX_MODEL_BYTES", 1), patch.object(model_cache, "urlopen", return_value=io.BytesIO(self.content)):
            with self.assertRaisesRegex(ValueError, "size limit"):
                model_cache.ensure_model(self.name)
        self.assertEqual([], list(self.cache.iterdir()))


if __name__ == "__main__":
    unittest.main()
