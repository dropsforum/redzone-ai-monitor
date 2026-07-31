#!/usr/bin/env python3
"""Create a blank benchmark result file outside the repository by default."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def default_output() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "redzone-ai-monitor" / "benchmark-results.json"
    return Path.home() / ".cache" / "redzone-ai-monitor" / "benchmark-results.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a benchmark capture template.")
    parser.add_argument("--output", type=Path, default=default_output(), help="JSON result path.")
    parser.add_argument("--dry-run", action="store_true", help="Print the template without writing it.")
    return parser.parse_args()


def template() -> dict[str, object]:
    return {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "experiment": {
            "model": "YOLO26n",
            "input_size": [640, 640],
            "source": "representative red-zone footage; document clip IDs without storing footage here",
            "warmup_runs": 10,
            "measured_runs": 100,
        },
        "acceptance_criteria": {
            "latency_improvement_min_percent": 20.0,
            "max_breach_recall_loss_percentage_points": 1.0,
            "max_missed_breach_increase": 0,
            "false_alerts_per_hour_must_not_increase": True,
            "fallback_and_packaging_regression": False,
        },
        "comparisons": [
            {
                "platform": "browser",
                "baseline": result_block("onnx-wasm"),
                "candidate": result_block("litert-webgpu", candidate=True),
                "promotion_decision": "not_evaluated",
            },
            {
                "platform": "mac",
                "baseline": result_block("pytorch-mps"),
                "candidate": result_block("coreml-fp16", candidate=True),
                "promotion_decision": "not_evaluated",
            },
        ],
    }


def result_block(backend: str, candidate: bool = False) -> dict[str, object]:
    result: dict[str, object] = {
        "backend": backend,
        "model_sha256": "",
        "device": "",
        "runtime_versions": {},
        "preprocess_ms": {"median": None, "p95": None},
        "inference_ms": {"median": None, "p95": None},
        "postprocess_ms": {"median": None, "p95": None},
        "end_to_end_ms": {"median": None, "p95": None},
        "observed_fps": None,
        "breach_recall": None,
        "false_alerts_per_hour": None,
        "missed_breaches": None,
        "notes": "",
    }
    if candidate:
        result["fallback_verified"] = False
        result["packaging_verified"] = False
    return result


def main() -> int:
    args = parse_args()
    rendered = json.dumps(template(), indent=2) + "\n"
    if args.dry_run:
        print(rendered, end="")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote benchmark template: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
