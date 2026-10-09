import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_ai_app


class NativeLauncherTests(unittest.TestCase):
    def test_self_test_defaults_to_external_application_data(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            sys, "argv", ["run_ai_app.py", "--self-test"]
        ), patch("ai_motion_app.platform_utils.get_app_data_dir", return_value=Path(temporary)), patch(
            "ai_motion_app.self_test.run_self_test", return_value=0
        ) as run:
            self.assertEqual(run_ai_app.main(), 0)
            run.assert_called_once_with(Path(temporary) / "self-test.json", "auto")

    def test_explicit_relative_self_test_path_is_preserved(self):
        with patch.object(sys, "argv", ["run_ai_app.py", "--self-test", "--self-test-output", "report.json"]), patch(
            "ai_motion_app.self_test.run_self_test", return_value=0
        ) as run:
            self.assertEqual(run_ai_app.main(), 0)
            run.assert_called_once_with(Path("report.json"), "auto")

    def test_mac_runtime_hook_keeps_callers_directory(self):
        original = Path.cwd()
        hook = Path(__file__).resolve().parents[2] / "packaging/macos/runtime_hook.py"
        with tempfile.TemporaryDirectory() as temporary, patch.object(
            sys, "_MEIPASS", temporary, create=True
        ), patch.dict(os.environ):
            runpy.run_path(str(hook))
        self.assertEqual(Path.cwd(), original)


if __name__ == "__main__":
    unittest.main()
