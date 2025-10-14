# PyInstaller spec for DROPS Red Zone Monitoring POC (arm64, unsigned)
# Builds a windowed .app that launches the OpenCV UI without a Terminal

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# When running spec, __file__ may not be defined; use CWD as project root
project_root = os.path.abspath(os.getcwd())

# Hidden imports for dynamic packages
hiddenimports = []
for pkg in [
    "cv2",
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
if os.path.exists(os.path.join(project_root, "yolov8n.pt")):
    local_datas.append((os.path.join(project_root, "yolov8n.pt"), "."))
zone_cfg = os.path.join(project_root, "zones", "zone_config.json")
if os.path.exists(zone_cfg):
    local_datas.append((zone_cfg, os.path.join("zones")))

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
    a.binaries,
    a.zipfiles,
    a.datas,
    name="DROPS Red Zone Monitoring POC",
    console=False,
    disable_windowed_traceback=False,
)

app = BUNDLE(
    exe,
    name="DROPS Red Zone Monitoring POC.app",
    icon=None,  # Provide packaging/macos/icon.icns if available
    bundle_identifier="com.drops.redzone.poc",
    info_plist={
        "NSCameraUsageDescription": "Camera access is required to monitor the zone.",
        "CFBundleName": "DROPS Red Zone Monitoring POC",
        "LSMinimumSystemVersion": "12.0",
    },
)


