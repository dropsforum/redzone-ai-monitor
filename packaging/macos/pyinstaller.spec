# PyInstaller spec for Exposure Zone Monitoring (macOS arm64)
# Builds a windowed .app that launches the fast native Python/OpenCV app.

import os
from importlib import metadata
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, copy_metadata

block_cipher = None

# When running spec, __file__ may not be defined; use CWD as project root
project_root = os.path.abspath(os.getcwd())
from ai_motion_app.version import APP_NAME, MAC_BUNDLE_VERSION, MAC_BUILD_NUMBER

# Ultralytics loads task modules dynamically. Torch, torchvision, pygame and
# Pillow are covered by their PyInstaller hooks; collecting every submodule
# would also bundle their test suites and considerably slow Mac packaging.
hiddenimports = collect_submodules("ultralytics")

# Data files these libs need at runtime
datas = []
for pkg in [
    "ultralytics",
    "torch",
    "torchvision",
    "pygame",
    "PIL",
]:
    try:
        datas.extend(collect_data_files(pkg))
    except Exception:
        pass

# Models and user data must never be copied from the developer's checkout.
for filename in ["LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "PACKAGE_README.md"]:
    datas.append((os.path.join(project_root, filename), "."))
datas.append((os.path.join(project_root, "docs", "desktop-releases.md"), "docs"))
datas.append((os.path.join(project_root, "docs", "yolo26-model-ops.md"), "docs"))
datas.append((os.path.join(project_root, "packaging", "macos", "Python-LICENSE.txt"), "licenses"))
for filename in ["LGPL-3.0.txt", "GPL-3.0.txt"]:
    datas.append((os.path.join(project_root, "packaging", "licenses", filename), "licenses"))
for distribution in ["ultralytics", "torch", "torchvision", "PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6", "opencv-python", "numpy", "pygame", "Pillow"]:
    datas.extend(copy_metadata(distribution))

# Include the license texts of transitive dependencies, not just direct wheels.
for distribution in metadata.distributions():
    for entry in distribution.files or ():
        parts = entry.parts
        info_index = next((i for i, part in enumerate(parts) if part.endswith(".dist-info")), None)
        if info_index is None or not any("license" in part.lower() or "notice" in part.lower() for part in parts):
            continue
        source = Path(distribution.locate_file(entry))
        if source.is_file():
            destination = Path("licenses").joinpath(*parts[info_index:-1])
            datas.append((str(source), str(destination)))

a = Analysis(
    [os.path.join(project_root, "run_ai_app.py")],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[os.path.join(project_root, "packaging", "macos", "runtime_hook.py")],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)

app = BUNDLE(
    coll,
    name=f"{APP_NAME}.app",
    icon=None,  # Provide packaging/macos/icon.icns if available
    bundle_identifier="com.drillingvr.drops-red-zone-monitoring",
    info_plist={
        "NSCameraUsageDescription": "Exposure Zone Monitoring uses the camera to analyze safety footage locally on this Mac.",
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleShortVersionString": MAC_BUNDLE_VERSION,
        "CFBundleVersion": MAC_BUILD_NUMBER,
        "LSMinimumSystemVersion": "14.0",
        "LSApplicationCategoryType": "public.app-category.utilities",
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeName": "Video File",
                "CFBundleTypeRole": "Viewer",
                "LSHandlerRank": "Alternate",
                "LSItemContentTypes": [
                    "public.movie",
                    "public.mpeg-4",
                    "com.apple.quicktime-movie",
                    "public.avi",
                ],
            }
        ],
    },
)
