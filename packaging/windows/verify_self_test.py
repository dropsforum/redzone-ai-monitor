"""Run the windowed frozen executable synchronously and gate its JSON report."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "dist/DROPS Red Zone Monitoring/DROPS Red Zone Monitoring.exe"
REPORT = ROOT / "dist/self-test.json"


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
    if not isinstance(payload, dict) or payload.get("success") is not True:
        raise RuntimeError("Frozen self-test must report JSON success=true")
    return payload


if __name__ == "__main__":
    run_self_test()
