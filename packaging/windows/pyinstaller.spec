# PyInstaller spec for DROPS Red Zone Monitoring (Windows)
# Builds a windowed .exe that launches the OpenCV UI without a console window

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
    "winsound",  # Windows sound support
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
if os.path.exists(os.path.join(project_root, "models", "yolov8n.pt")):
    local_datas.append((os.path.join(project_root, "models", "yolov8n.pt"), "."))
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
    runtime_hooks=[],  # Windows doesn't need runtime hooks typically
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="DROPS Red Zone Monitoring",
    console=False,  # Windowed mode (no console)
    disable_windowed_traceback=False,
    icon=None,  # Provide packaging/windows/icon.ico if available
    version=None,  # Provide version info file if available
)


