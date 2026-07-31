#!/usr/bin/env python3
"""Create a reproducible, privacy-conscious provenance manifest for model artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

EXPECTED_ULTRALYTICS = "8.4.112"


def default_output() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "redzone-ai-monitor" / "provenance.json"
    return Path.home() / ".cache" / "redzone-ai-monitor" / "provenance.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hash model files/directories and write a provenance JSON manifest."
    )
    parser.add_argument("artifacts", nargs="+", type=Path, help="Model file or package directory.")
    parser.add_argument("--output", type=Path, default=default_output(), help="Manifest path.")
    parser.add_argument("--source-model", default="yolo26n.pt", help="Source checkpoint name.")
    parser.add_argument(
        "--ultralytics-version",
        default=EXPECTED_ULTRALYTICS,
        help=f"Exporter version (default: {EXPECTED_ULTRALYTICS}).",
    )
    parser.add_argument("--export-command", action="append", default=[], help="Exact command used; repeatable.")
    parser.add_argument("--dry-run", action="store_true", help="Print the manifest without writing it.")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_hash(path: Path) -> tuple[str, int]:
    if path.is_file():
        return sha256_file(path), path.stat().st_size
    if not path.is_dir():
        raise ValueError(f"Artifact does not exist: {path}")

    digest = hashlib.sha256()
    total_size = 0
    for child in sorted(p for p in path.rglob("*") if p.is_file()):
        relative = child.relative_to(path).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        child_hash = sha256_file(child).encode("ascii")
        digest.update(child_hash)
        digest.update(b"\0")
        total_size += child.stat().st_size
    return digest.hexdigest(), total_size


def expected_export_profile(path: Path) -> dict[str, object]:
    suffix = path.suffix.lower()
    if suffix == ".onnx":
        return {
            "format": "onnx",
            "imgsz": 640,
            "batch": 1,
            "opset": 17,
            "simplify": False,
            "dynamic": False,
            "end2end": True,
            "output": "[1,300,6] xyxy, confidence, class_id; no extra NMS",
        }
    if suffix == ".tflite":
        return {
            "format": "litert",
            "imgsz": 640,
            "batch": 1,
            "end2end": False,
            "output": "traditional detection head; official browser package performs NMS",
        }
    if suffix in {".mlpackage", ".mlmodel", ".mlmodelc"}:
        return {
            "format": "coreml",
            "imgsz": 640,
            "batch": 1,
            "quantize": 16,
            "end2end": False,
            "output": "traditional detection head; Ultralytics performs postprocessing",
        }
    return {"format": "unknown"}


def build_manifest(args: argparse.Namespace) -> dict[str, object]:
    entries = []
    for artifact in args.artifacts:
        digest, size = artifact_hash(artifact)
        entries.append(
            {
                "name": artifact.name,
                "kind": "directory" if artifact.is_dir() else "file",
                "size_bytes": size,
                "sha256": digest,
                "expected_export_profile": expected_export_profile(artifact),
            }
        )
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_model": args.source_model,
        "ultralytics_version": args.ultralytics_version,
        "expected_input_shape": [1, 3, 640, 640],
        "runtime_policy": {
            "browser_default": "onnxruntime-web WASM",
            "browser_experimental": "LiteRT/WebGPU after benchmark validation",
            "mac_default": "Ultralytics PyTorch/MPS",
            "mac_experimental": "CoreML FP16 after benchmark validation",
        },
        "export_commands": args.export_command,
        "artifacts": entries,
    }


def main() -> int:
    args = parse_args()
    manifest = build_manifest(args)
    rendered = json.dumps(manifest, indent=2) + "\n"
    if args.dry_run:
        print(rendered, end="")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote provenance manifest: {args.output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
