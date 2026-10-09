"""Run the windowed frozen executable synchronously and gate its JSON report."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "dist/DROPS Red Zone Monitoring/DROPS Red Zone Monitoring.exe"
REPORT = ROOT / "dist/self-test.json"
EXPECTED_FIELDS = {
    "version": "1.2.0-rc.1",
    "platform": "Windows",
    "model": "yolo26n-seg.pt",
    "ultralytics": "8.4.146",
    "backend": "pytorch/cpu",
}
EXPECTED_CHECKS = {
    "recorded-video-decoding-and-normal-speed-playback",
    "qt-rendering-and-draggable-zone-corners",
    "silhouette-contact-entry-and-exit-grace",
    "sqlite-and-five-sheet-excel-report",
    "verified-model-download-segmentation-tracking-and-inference",
}


def validate_report(payload):
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise RuntimeError("Frozen self-test must report JSON success=true")
    for field, expected in EXPECTED_FIELDS.items():
        if type(payload.get(field)) is not str or payload[field] != expected:
            raise RuntimeError(f"Frozen self-test must report {field}={expected!r}")
    checks = payload.get("checks")
    if (
        type(checks) is not list
        or len(checks) != len(EXPECTED_CHECKS)
        or any(type(check) is not str for check in checks)
        or set(checks) != EXPECTED_CHECKS
    ):
        raise RuntimeError("Frozen self-test must report exactly the five expected checks")


def run_self_test(executable=EXE, report=REPORT):
    executable, report = Path(executable).resolve(), Path(report).resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.unlink(missing_ok=True)
    result = subprocess.run(
        [str(executable), "--self-test", "--self-test-output", str(report)],
        cwd=ROOT, timeout=600, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Frozen self-test exited {result.returncode}")
    payload = json.loads(report.read_text(encoding="utf-8"))
    validate_report(payload)
    return payload


if __name__ == "__main__":
    run_self_test()
