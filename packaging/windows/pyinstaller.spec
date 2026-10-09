# Build from the repository root on Windows x64; no weights or user assets.
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

project_root = Path(SPECPATH).resolve().parents[1]
hiddenimports = collect_submodules(
    "ultralytics", filter=lambda name: ".tests" not in name and ".test_" not in name
)
datas = collect_data_files(
    "ultralytics",
    excludes=["**/tests/**", "**/*.pt", "**/*.onnx", "**/*.mp4", "**/*.avi"],
)

# Standard PyInstaller/hooks-contrib hooks own torch, torchvision, cv2,
# PySide6, numpy, Pillow and pygame. Do not recursively collect those modules.
a = Analysis(
    [str(project_root / "run_ai_app.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[str(project_root / "packaging/windows/runtime_hook.py")],
    excludes=[
        "pytest", "tkinter", "IPython", "tensorflow", "tensorboard",
        "jax", "jaxlib", "transformers", "onnx", "onnxruntime", "coremltools",
        "openvino", "tensorrt", "matplotlib.tests", "numpy.tests", "scipy.tests",
    ],
    noarchive=False,
)
# Standard dependency hooks may collect their own test fixtures. They are not
# application resources and must not enter the downloadable payload.
a.datas = [entry for entry in a.datas if "tests" not in Path(entry[0]).parts]
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name="ExposureZoneMonitoring", console=False,
    disable_windowed_traceback=False, strip=False, upx=False,
    version=str(project_root / "packaging/windows/version_info.txt"),
)
coll = COLLECT(
    exe, a.binaries, a.datas, strip=False, upx=False,
    name="Exposure Zone Monitoring",
)
