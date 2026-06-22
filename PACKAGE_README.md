# redzone-web-app Integration Package

This package contains the Next.js browser-based YOLO detection module for integration into `dropsforum.org`.

## What's included

- **AI Engine**: Client-side YOLO26 (ONNX Runtime Web)
- **UI Components**: Camera/recorded-video frame source, Touch-friendly Zone Editor, Detection Overlay
- **Logic**: Zone intrusion detection, Alert system
- **Performance**: Optimized for Desktop (10 FPS) and Mobile (3 FPS)

## Local Development

To run this app locally for testing:

1. **Install dependencies**: `npm install`
2. **Launch server**: `npm run dev`
3. **Open browser**: Go to `http://localhost:3000` (or `http://localhost:3001` if 3000 is occupied).

**Note for Production Builds**: If you are using Next.js 15+, ensure you use the `--webpack` flag in your build command (e.g., `next build --webpack`) to support the custom Webpack configuration required for the ONNX models.

## How to integrate into dropsforum.org

### 1. Copy Files
Copy these directories into your `dropsforum.org` project:
- `src/components/*` -> `components/`
- `src/lib/*` -> `lib/`
- `public/wasm/*` -> `public/wasm/`

Model binaries are intentionally not committed to this public package. Generate `public/models/yolo26n.onnx` locally from Ultralytics before running detection.

### 2. Install Dependencies
Run this in your website project:
```bash
npm install onnxruntime-web lucide-react clsx tailwind-merge
```

### 3. Serve ONNX Runtime assets
Copy the matching ONNX Runtime Web distribution files into `public/wasm`:
```bash
rm -rf public/wasm/*
cp node_modules/onnxruntime-web/dist/* public/wasm/
```

### 4. Use the Monitoring Page
Copy `src/app/page.tsx` (or its contents) to your desired route (e.g., `app/redzone/page.tsx`).

## Note on Mobile Performance
The app automatically detects mobile devices and reduces inference frequency and resolution to preserve battery and performance.

## Model Provenance

- Model file: `public/models/yolo26n.onnx`
- Source model: `yolo26n.pt` from Ultralytics assets, downloaded/exported locally by each user
- Model binaries: intentionally excluded from this public repository
- Export toolchain: `ultralytics==8.4.68`, `onnx==1.20.0`, Python 3.12
- Export command: `YOLO("yolo26n.pt").export(format="onnx", imgsz=640, opset=17, simplify=False)`
- Expected input shape: `(1, 3, 640, 640)`
- Expected output shape: `(1, 300, 6)`

Example local export:

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
