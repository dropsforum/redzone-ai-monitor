"""Verified first-use model downloads; checkpoints are not release assets."""

from __future__ import annotations

import hashlib
import os
import platform
import tempfile
from pathlib import Path
from typing import Callable
from urllib.request import urlopen

MODEL_ASSETS = {
    "yolo26n.pt": "9b09cc8bf347f0fc8a5f7657480587f25db09b34bf33b0652110fb03a8ad4fef",
    "yolo26n-seg.pt": "361fbfabab285c3237700b6bb91d7ecfa602cd945fffda8dbe1242829b71e73f",
}
MODEL_SOURCE = "https://github.com/ultralytics/assets/releases/download/v8.4.0/"
MAX_MODEL_BYTES = 64 * 1024 * 1024


def model_cache_dir() -> Path:
    override = os.environ.get("REDZONE_MODEL_CACHE")
    if override:
        return Path(override).expanduser()
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Caches" / "redzone-ai-monitor" / "models"
    if platform.system() == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "DROPS Red Zone Monitoring" / "models"
    return Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "redzone-ai-monitor" / "models"


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(256 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_model(name: str, status: Callable[[str], None] | None = None) -> Path:
    if name not in MODEL_ASSETS:
        raise ValueError(f"No approved download is configured for {name}")
    target = model_cache_dir() / name
    expected = MODEL_ASSETS[name]
    if target.is_file() and file_digest(target) == expected:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    if status:
        status("Downloading AI model")
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{name}.", suffix=".part", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        total = 0
        digest = hashlib.sha256()
        with os.fdopen(descriptor, "wb") as output, urlopen(MODEL_SOURCE + name, timeout=30) as response:
            while chunk := response.read(256 * 1024):
                total += len(chunk)
                if total > MAX_MODEL_BYTES:
                    raise ValueError("Model download exceeded the expected size limit")
                output.write(chunk)
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise ValueError(f"SHA-256 verification failed for {name}")
        os.replace(temporary, target)
        return target
    finally:
        temporary.unlink(missing_ok=True)
