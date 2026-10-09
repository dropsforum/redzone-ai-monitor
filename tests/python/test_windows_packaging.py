import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
WINDOWS = ROOT / "packaging/windows"


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, WINDOWS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = load_module("build")
self_test = load_module("verify_self_test")


class WindowsPackagingTests(unittest.TestCase):
    def make_app(self, root):
        app = Path(root) / build.APP_NAME
        app.mkdir()
        (app / f"{build.APP_NAME}.exe").write_bytes(b"test-executable")
        (app / "_internal").mkdir()
        (app / "_internal/runtime.dll").write_bytes(b"test-dll")
        return app

    def test_archive_contains_only_onedir_and_matching_checksum(self):
        with tempfile.TemporaryDirectory() as directory:
            app = self.make_app(directory)
            (Path(directory) / "unrelated-secret.txt").write_text("not shipped")
            output = Path(directory) / build.ZIP.name
            build.archive(app, output)
            with zipfile.ZipFile(output) as bundle:
                self.assertEqual(set(bundle.namelist()), {
                    f"{build.APP_NAME}/{build.APP_NAME}.exe",
                    f"{build.APP_NAME}/_internal/runtime.dll",
                })
            expected = hashlib.sha256(output.read_bytes()).hexdigest()
            self.assertEqual(output.with_suffix(".zip.sha256").read_text(),
                             f"{expected}  {output.name}\n")

    def test_rejects_private_files_models_and_test_artifacts(self):
        for name in (
            "yolo26n-seg.pt", "weights.onnx", "clip.mp4", "private.sqlite3",
            ".env.local", "config.json", "settings.json", "credentials.json",
            "build.log", "key.pfx", "self-test.json", "tests/example.py",
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                app = self.make_app(directory)
                bad = app / "_internal" / name
                bad.parent.mkdir(parents=True, exist_ok=True)
                bad.write_text("forbidden")
                with self.assertRaisesRegex(RuntimeError, "Forbidden release payload"):
                    build.archive(app, Path(directory) / "release.zip")
                self.assertFalse((Path(directory) / "release.zip").exists())

    def test_rejects_missing_executable(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "Missing frozen executable"):
                build.validate_payload(directory)

    def test_documents_include_selected_notices_python_and_wheel_licenses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app = self.make_app(root)
            for name in (
                "LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "requirements_windows.txt", "LICENSE.txt",
                "packaging/windows/README.md", "docs/desktop-releases.md",
                "docs/yolo26-model-ops.md", "demo-1.dist-info/licenses/LICENSE",
            ):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("test notice")
            (root / "private.sqlite3").write_bytes(b"not shipped")
            (root / "THIRD_PARTY_NOTICES.md").write_text("canonical root notices")
            (root / "docs/desktop-releases.md").write_text("canonical desktop guide")
            dist = types.SimpleNamespace(
                metadata={"Name": "demo"}, version="1.0",
                files=[Path("demo-1.dist-info/licenses/LICENSE")],
                locate_file=lambda entry: root / entry,
            )
            with patch.object(build, "ROOT", root), patch.object(build.sys, "base_prefix", str(root)), patch.object(build.metadata, "distributions", return_value=[dist]):
                build.add_documents(app)
            self.assertTrue((app / "LICENSE").is_file())
            self.assertTrue((app / "NOTICE").is_file())
            self.assertEqual((app / "THIRD_PARTY_NOTICES.md").read_bytes(),
                             (root / "THIRD_PARTY_NOTICES.md").read_bytes())
            self.assertEqual((app / "docs/desktop-releases.md").read_bytes(),
                             (root / "docs/desktop-releases.md").read_bytes())
            self.assertTrue((app / "licenses/Python-LICENSE.txt").is_file())
            self.assertTrue((app / "licenses/demo-1.dist-info/licenses/LICENSE").is_file())
            manifest = json.loads((app / "docs/build-dependencies.json").read_text())
            self.assertEqual(manifest["dependencies"], {"demo": "1.0"})
            self.assertEqual(manifest["version"], "1.2.0-rc.1")
            self.assertFalse((app / "private.sqlite3").exists())
            build.validate_payload(app)

    def test_build_refuses_cross_compilation(self):
        with patch.object(build.sys, "platform", "darwin"), patch.object(build.sys, "argv", ["build.py"]):
            with self.assertRaisesRegex(RuntimeError, "Native Windows x64"):
                build.main()

    def test_self_test_waits_and_requires_fresh_success(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "self-test.json"
            report.write_text('{"success": true, "stale": true}')

            def run(command, **kwargs):
                self.assertFalse(report.exists())
                self.assertEqual(command[1:3], ["--self-test", "--self-test-output"])
                self.assertEqual(Path(command[3]), report.resolve())
                self.assertEqual(kwargs["timeout"], 600)
                report.write_text('{"success": true}')
                return subprocess.CompletedProcess(command, 0)

            with patch.object(self_test.subprocess, "run", side_effect=run):
                self.assertEqual(self_test.run_self_test(Path(directory) / "app.exe", report), {"success": True})

    def test_self_test_rejects_failure_missing_invalid_and_false_reports(self):
        for returncode, payload in (
            (1, '{"success":true}'), (0, None), (0, "invalid"),
            (0, '{"success":false}'), (0, '{"success":"true"}'), (0, "[]"),
        ):
            with self.subTest(returncode=returncode, payload=payload), tempfile.TemporaryDirectory() as directory:
                report = Path(directory) / "self-test.json"

                def run(command, **kwargs):
                    if payload is not None:
                        report.write_text(payload)
                    return subprocess.CompletedProcess(command, returncode)

                with patch.object(self_test.subprocess, "run", side_effect=run):
                    with self.assertRaises((RuntimeError, FileNotFoundError, json.JSONDecodeError)):
                        self_test.run_self_test(Path(directory) / "app.exe", report)

    def test_self_test_timeout_is_a_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(self_test.subprocess, "run", side_effect=subprocess.TimeoutExpired("app.exe", 600)):
                with self.assertRaises(subprocess.TimeoutExpired):
                    self_test.run_self_test(Path(directory) / "app.exe", Path(directory) / "report.json")

    def test_spec_uses_ultralytics_dynamic_collection_only(self):
        calls = []
        hook_module = types.ModuleType("PyInstaller.utils.hooks")

        def collect_submodules(package, **kwargs):
            calls.append(package)
            self.assertTrue(kwargs["filter"]("ultralytics.models.yolo"))
            self.assertFalse(kwargs["filter"]("ultralytics.tests"))
            return ["ultralytics.models.yolo"]

        hook_module.collect_submodules = collect_submodules
        hook_module.collect_data_files = lambda *args, **kwargs: []
        analyses = []

        def analysis(*args, **kwargs):
            analyses.append(kwargs)
            return types.SimpleNamespace(pure=[], scripts=[], binaries=[], datas=[])

        with patch.dict("sys.modules", {"PyInstaller.utils.hooks": hook_module}):
            runpy.run_path(str(WINDOWS / "pyinstaller.spec"), init_globals={
                "SPECPATH": str(WINDOWS), "Analysis": analysis,
                "PYZ": lambda *args: None, "EXE": lambda *args, **kwargs: None,
                "COLLECT": lambda *args, **kwargs: None,
            })
        self.assertEqual(calls, ["ultralytics"])
        self.assertEqual(analyses[0]["datas"], [])
        self.assertEqual(analyses[0]["runtime_hooks"], [str(WINDOWS / "runtime_hook.py")])

    def test_runtime_hook_preserves_cwd_without_mac_loader(self):
        import os
        original = Path.cwd()
        with patch.dict(os.environ, {}, clear=True):
            runpy.run_path(str(WINDOWS / "runtime_hook.py"))
            self.assertEqual(os.environ["YOLO_AUTOINSTALL"], "false")
            self.assertEqual(Path.cwd(), original)

    def test_workflow_is_bounded_read_only_and_unpublished(self):
        # BaseLoader avoids YAML 1.1 treating GitHub's `on` key as a boolean.
        import yaml
        workflow = yaml.load((ROOT / ".github/workflows/desktop-windows.yml").read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(set(workflow["on"]), {"push", "workflow_dispatch"})
        self.assertEqual(workflow["on"]["push"]["branches"], ["codex/native-desktop-release"])
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        job = workflow["jobs"]["windows-x64"]
        self.assertEqual(job["runs-on"], "windows-2022")
        self.assertEqual(job["timeout-minutes"], "45")
        self.assertEqual(job["env"]["QT_QPA_PLATFORM"], "offscreen")
        commands = "\n".join(step.get("run", "") for step in job["steps"])
        self.assertIn("https://download.pytorch.org/whl/cpu", commands)
        self.assertIn("torch==2.12.0+cpu torchvision==0.27.0+cpu", commands)
        self.assertNotIn("${{", commands)
        self.assertNotIn("gh release", commands)
        steps = [step.get("name") for step in job["steps"]]
        self.assertLess(steps.index("Verify frozen self-test"), steps.index("Archive verified payload and SHA256"))


if __name__ == "__main__":
    unittest.main()
