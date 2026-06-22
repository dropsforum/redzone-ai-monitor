# PyInstaller spec for DROPS Red Zone Monitoring (macOS arm64)
# Builds a windowed .app that launches the fast native Python/OpenCV app.

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# When running spec, __file__ may not be defined; use CWD as project root
project_root = os.path.abspath(os.getcwd())

# Hidden imports for dynamic packages
hiddenimports = []
for pkg in [
    "ultralytics",
    "torch",
    "torchvision",
    "pygame",
    "PIL",
]:
    try:
        hiddenimports.extend(collect_submodules(pkg))
    except Exception:
        pass

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

# Bundle local model and zone config if present
local_datas = []
for model_path in [
    Path(project_root) / "models" / "yolo26n.pt",
    Path(project_root) / "yolo26n.pt",
]:
    if model_path.exists():
        local_datas.append((str(model_path), "models"))

for asset_dir in [
    Path(project_root) / "assets",
]:
    if asset_dir.exists():
        local_datas.append((str(asset_dir), asset_dir.name))

datas.extend(local_datas)

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
    name="DROPS Red Zone Monitoring",
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
    name="DROPS Red Zone Monitoring",
)

app = BUNDLE(
    coll,
    name="DROPS Red Zone Monitoring.app",
    icon=None,  # Provide packaging/macos/icon.icns if available
    bundle_identifier="com.drillingvr.drops-red-zone-monitoring",
    info_plist={
        "NSCameraUsageDescription": "DROPS Red Zone Monitor uses the camera to analyze red-zone safety footage locally on this Mac.",
        "CFBundleName": "DROPS Red Zone Monitoring",
        "CFBundleDisplayName": "DROPS Red Zone Monitoring",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "1",
        "LSMinimumSystemVersion": "12.0",
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
