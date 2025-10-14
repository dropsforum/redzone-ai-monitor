import os
import sys

# Ensure working directory points inside the app bundle for relative paths
base = getattr(sys, '_MEIPASS', None)
if base:
    try:
        os.chdir(base)
    except Exception:
        pass

# Prefer Metal (MPS) backend when available; allow fallback
os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')



