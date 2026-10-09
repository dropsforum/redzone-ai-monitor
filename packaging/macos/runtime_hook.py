import os
import sys
import importlib.util
from pathlib import Path

# Keep caller-relative video/report paths outside the signed bundle.
base = getattr(sys, '_MEIPASS', None)
if base:
    cv2_extension = Path(base) / "cv2" / "cv2.abi3.so"
    if cv2_extension.exists() and "cv2" not in sys.modules:
        spec = importlib.util.spec_from_file_location("cv2", cv2_extension)
        if spec and spec.loader:
            cv2_module = importlib.util.module_from_spec(spec)
            sys.modules["cv2"] = cv2_module
            spec.loader.exec_module(cv2_module)

# Prefer Metal (MPS) backend when available; allow fallback
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')

