# Local Model Directory

Model binaries are intentionally not committed to this public repository.
The existing `.gitignore` excludes generated ONNX, LiteRT and CoreML artifacts.

Generate the browser model with the pinned exporter:

```bash
python -m pip install ultralytics==8.4.112 onnx
python scripts/export_yolo26n.py \
  --format onnx \
  --weights yolo26n.pt \
  --output-dir public/models \
  --force
```

This is a YOLO26 end-to-end export with input `640 x 640`, ONNX opset 17,
batch 1, and expected output `(1, 300, 6)`. It is the browser's default model
artifact. LiteRT and CoreML exports are experimental and default to a cache
outside the repository; see [`docs/yolo26-model-ops.md`](../../docs/yolo26-model-ops.md).

Users are responsible for complying with Ultralytics model and tooling license terms.
