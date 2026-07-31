#!/usr/bin/env python3
"""Export the official YOLO26n checkpoint to approved experimental formats.

The script deliberately writes to a user cache by default. Use an explicit
output directory when producing the browser ONNX artifact.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

EXPECTED_ULTRALYTICS = "8.4.112"
FORMATS = ("onnx", "litert", "coreml", "all")


def default_output_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "redzone-ai-monitor" / "yolo26n-exports"
    return Path.home() / ".cache" / "redzone-ai-monitor" / "yolo26n-exports"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export YOLO26n with the Red Zone app's reproducible settings."
    )
    parser.add_argument(
        "--format",
        choices=FORMATS,
        default="onnx",
        help="Artifact format to export (default: onnx).",
    )
    parser.add_argument(
        "--weights",
        type=Path,
        default=Path("yolo26n.pt"),
        help="Local YOLO26n checkpoint path (default: yolo26n.pt).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(),
        help="Destination directory; defaults outside the repository.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing artifact at the destination.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print export settings without importing Ultralytics or writing files.",
    )
    return parser.parse_args()


def settings_for(format_name: str) -> dict[str, Any]:
    if format_name == "onnx":
        return {
            "format": "onnx",
            "imgsz": 640,
            "opset": 17,
            "simplify": False,
            "end2end": True,
            "batch": 1,
            "dynamic": False,
        }
    if format_name == "litert":
        return {
            "format": "litert",
            "imgsz": 640,
            "batch": 1,
            "end2end": False,
        }
    if format_name == "coreml":
        return {
            "format": "coreml",
            "imgsz": 640,
            "quantize": 16,
            "batch": 1,
            "end2end": False,
        }
    raise ValueError(f"Unsupported export format: {format_name}")


def destination_name(format_name: str) -> str:
    return {
        "onnx": "yolo26n.onnx",
        "litert": "yolo26n.tflite",
        "coreml": "yolo26n.mlpackage",
    }[format_name]


def print_plan(args: argparse.Namespace, formats: list[str]) -> None:
    print(f"Ultralytics version required: {EXPECTED_ULTRALYTICS}")
    print(f"Weights: {args.weights}")
    print(f"Output directory: {args.output_dir}")
    for format_name in formats:
        print(f"\n[{format_name}] {destination_name(format_name)}")
        for key, value in settings_for(format_name).items():
            print(f"  {key}={value!r}")


def installed_ultralytics_version() -> str:
    try:
        return importlib.metadata.version("ultralytics")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError(
            "Ultralytics is not installed. Run: "
            f"python -m pip install ultralytics=={EXPECTED_ULTRALYTICS}"
        ) from exc


def copy_artifact(source: Path, destination: Path, force: bool) -> None:
    if not source.exists():
        raise RuntimeError(f"Ultralytics reported a missing export: {source}")
    if destination.exists():
        if not force:
            raise RuntimeError(f"Destination exists; rerun with --force: {destination}")
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def export_one(weights: Path, format_name: str, output_dir: Path, force: bool) -> Path:
    try:
        from ultralytics import YOLO
    except ImportError as exc:
        raise RuntimeError(
            "Ultralytics is not installed. Run: "
            f"python -m pip install ultralytics=={EXPECTED_ULTRALYTICS}"
        ) from exc

    destination = output_dir / destination_name(format_name)
    with tempfile.TemporaryDirectory(prefix=f"redzone-{format_name}-export-") as directory:
        temporary_weights = Path(directory) / weights.name
        shutil.copy2(weights.resolve(), temporary_weights)
        model = YOLO(str(temporary_weights))
        exported = model.export(**settings_for(format_name))
        if isinstance(exported, (list, tuple)):
            exported = exported[0]
        source = Path(os.fspath(exported))
        copy_artifact(source, destination, force)
    return destination


def main() -> int:
    args = parse_args()
    formats = ["onnx", "litert", "coreml"] if args.format == "all" else [args.format]
    print_plan(args, formats)
    if args.dry_run:
        return 0

    version = installed_ultralytics_version()
    if version != EXPECTED_ULTRALYTICS:
        raise RuntimeError(
            f"Expected ultralytics=={EXPECTED_ULTRALYTICS}, found {version}. "
            "Install the pinned version before exporting."
        )
    if not args.weights.exists():
        raise RuntimeError(f"Weights file not found: {args.weights}")

    for format_name in formats:
        destination = export_one(args.weights, format_name, args.output_dir, args.force)
        print(f"Exported {format_name}: {destination}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
