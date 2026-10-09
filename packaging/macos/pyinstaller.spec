# PyInstaller spec for DROPS Red Zone Monitoring (macOS arm64)
# Builds a windowed .app that launches the fast native Python/OpenCV app.

import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files, copy_metadata

block_cipher = None

# When running spec, __file__ may not be defined; use CWD as project root
project_root = os.path.abspath(os.getcwd())
from ai_motion_app.version import MAC_BUNDLE_VERSION, MAC_BUILD_NUMBER

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
for filename in ["LICENSE", "THIRD_PARTY_NOTICES.md"]:
    datas.append((os.path.join(project_root, filename), "."))
datas.append((os.path.join(project_root, "docs", "desktop-releases.md"), "docs"))
for distribution in ["ultralytics", "torch", "torchvision", "PySide6", "PySide6_Essentials", "PySide6_Addons", "shiboken6", "opencv-python", "numpy", "pygame", "Pillow"]:
    datas.extend(copy_metadata(distribution))

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
