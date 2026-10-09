"""Build native Windows onedir output and archive only that output and notices."""
import argparse
from hashlib import sha256
from importlib import metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
APP_NAME = "DROPS Red Zone Monitoring"
APP = ROOT / "dist" / APP_NAME
ZIP = ROOT / "dist/DROPS-Red-Zone-Monitoring-Windows-x64.zip"
VERSION = "1.2.0-rc.1"
FORBIDDEN_SUFFIXES = {
    ".pt", ".pth", ".onnx", ".engine", ".mlmodel", ".mlpackage",
    ".safetensors", ".ckpt", ".tflite",
    ".mp4", ".avi", ".mov", ".mkv", ".webm", ".log",
    ".sqlite", ".sqlite3", ".db", ".pem", ".key", ".pfx", ".p12",
}
FORBIDDEN_NAMES = {
    ".env", ".ds_store", "config.json", "settings.json", "credentials.json",
    "self-test.json", "id_rsa", "id_ed25519",
}


def is_verified_certifi_ca(path, relative):
    if relative.as_posix() != "_internal/certifi/cacert.pem" or not path.is_file():
        return False
    import certifi
    installed_ca = Path(certifi.where())
    return installed_ca.is_file() and sha256(path.read_bytes()).digest() == sha256(installed_ca.read_bytes()).digest()


def validate_payload(app):
    app = Path(app)
    if not (app / f"{APP_NAME}.exe").is_file():
        raise RuntimeError("Missing frozen executable")
    for path in app.rglob("*"):
        relative = path.relative_to(app)
        if path.is_symlink():
            raise RuntimeError(f"Symlink is not allowed: {relative}")
        parts = {part.lower() for part in relative.parts}
        if (
            (path.suffix.lower() in FORBIDDEN_SUFFIXES
             and not is_verified_certifi_ca(path, relative))
            or path.name.lower() in FORBIDDEN_NAMES
            or path.name.lower().startswith(".env.")
            or parts & {"logs", "videos", "user_data", ".git", "__pycache__", "tests"}
        ):
            raise RuntimeError(f"Forbidden release payload: {relative}")


def add_documents(app):
    docs = app / "docs"
    docs.mkdir(exist_ok=True)
    for name in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(ROOT / name, app / name)
    shutil.copy2(ROOT / "packaging/windows/README.md", app / "README.md")
    for name in ("yolo26-model-ops.md", "desktop-releases.md"):
        shutil.copy2(ROOT / "docs" / name, docs / name)
    shutil.copy2(ROOT / "requirements_windows.txt", docs / "requirements_windows.txt")
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if not python_license.is_file():
        raise RuntimeError(f"Missing CPython license: {python_license}")
    (app / "licenses").mkdir(exist_ok=True)
    shutil.copy2(python_license, app / "licenses/Python-LICENSE.txt")

    # Preserve license texts supplied by installed wheels, including Qt and
    # native-library notices. Record the actual resolved transitive versions.
    versions = {}
    for dist in metadata.distributions():
        name = dist.metadata["Name"]
        versions[name] = dist.version
        for entry in dist.files or ():
            parts = entry.parts
            if not any(part.endswith(".dist-info") for part in parts):
                continue
            if not any("license" in part.lower() or "notice" in part.lower() for part in parts):
                continue
            source = Path(dist.locate_file(entry))
            if not source.is_file():
                continue
            info_index = next(i for i, part in enumerate(parts) if part.endswith(".dist-info"))
            destination = app / "licenses" / parts[info_index]
            destination = destination.joinpath(*parts[info_index + 1:])
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    (docs / "build-dependencies.json").write_text(
        json.dumps({"version": VERSION, "python": platform.python_version(),
                    "dependencies": versions}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def archive(app=APP, output=ZIP):
    app, output = Path(app), Path(output)
    validate_payload(app)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(app.rglob("*")):
            if path.is_file():
                bundle.write(path, Path(APP_NAME) / path.relative_to(app))
    digest = sha256()
    with output.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    output.with_suffix(".zip.sha256").write_text(
        f"{digest.hexdigest()}  {output.name}\n", encoding="ascii",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", action="store_true", help="Archive after frozen self-test")
    args = parser.parse_args()
    if sys.platform != "win32" or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise RuntimeError("Native Windows x64 runner required; no cross-compilation")
    if args.archive:
        archive()
        return
    import torch
    import torchvision
    if torch.__version__ != "2.12.0+cpu" or torchvision.__version__ != "0.27.0+cpu" or torch.version.cuda is not None:
        raise RuntimeError("Expected pinned official CPU torch/torchvision wheels")
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "packaging/windows/pyinstaller.spec",
         "--clean", "--noconfirm"], cwd=ROOT, check=True,
    )
    add_documents(APP)
    validate_payload(APP)


if __name__ == "__main__":
    main()
