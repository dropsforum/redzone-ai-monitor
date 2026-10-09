"""Leave DLL/OpenCV/Qt loading to the platform-aware PyInstaller hooks."""
import os

# Frozen dependencies cannot be safely amended by an automatic pip install.
os.environ["YOLO_AUTOINSTALL"] = "false"
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
# Preserve cwd: relative video and --self-test-output paths belong to caller.
