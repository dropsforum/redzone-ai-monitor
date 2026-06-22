# Local Model Directory

Model binaries are intentionally not committed to this public repository.

Generate `yolo26n.onnx` locally before running browser inference:

```bash
python -m pip install ultralytics onnx
python - <<'PY'
from pathlib import Path
from ultralytics import YOLO

exported = YOLO("yolo26n.pt").export(format="onnx", imgsz=640, opset=17, simplify=False)
Path("public/models").mkdir(parents=True, exist_ok=True)
Path(exported).replace("public/models/yolo26n.onnx")
PY
```

Users are responsible for complying with Ultralytics model and tooling license terms.
