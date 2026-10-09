# Exposure Zone Monitoring - Web Integration Package

This package contains the Next.js browser-based Exposure Zone Monitoring module for integration into `dropsforum.org`. The product name is **Exposure Zone Monitoring**; the source repository remains `dropsforum/redzone-ai-monitor`.

This is a **web integration package**, not the native desktop download. The native Mac/Windows app uses Python/PySide6/OpenCV and `yolo26n-seg.pt` (`ultralytics==8.4.146`), with MPS on macOS 14+ Apple Silicon arm64 and CPU on Windows 10/11 x64. The browser uses YOLO26n ONNX/WASM detection with different geometry and foot-point zone checks; it does not have native segmentation parity. See [native preview downloads and installation](docs/desktop-releases.md) for `v1.2.0-rc.1`, its publication status and verification scope. Native binaries need no separate Python installation; website developers still need the web dependencies below.

Both targets are evaluation prototypes, not independent safety controls. Site-specific validation, human response, exposure reduction and privacy review remain necessary. Browser camera/file analysis is local, but this alone does not establish privacy compliance for the website into which it is integrated. Native SQLite persistence and five-sheet Excel reporting should not be assumed to exist in this web module.

See the [project philosophy and DROPS Asia/DROPS Forum implementation support](README.md#philosophy): avoid or reduce exposure first, then use monitoring for assurance and learning. The public [DROPS Forum article](https://www.dropsforum.org/red-zone-management#guidance) discusses the shift to Exposure Zone Management; the [full guidelines](https://www.dropsforum.org/publications/exposure-zone-management) remain a working draft, not an endorsed standard. Planning/workshop support does not provide technical enforcement or transfer site-owner accountability. Use the [official contact page](https://www.dropsforum.org/contact) for enquiries.

Consult the exact preview release notes and build manifest for download verification and limitations. Web header/metadata branding changes are source changes, not confirmation of a Vercel deployment. Native session/cache folders retain their legacy names intentionally for compatibility; they are not renamed by this web package.

## What's included

- **Local Inference**: ONNX Runtime Web (see technical model provenance below)
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
- Export toolchain: `ultralytics==8.4.112`, `onnx`, Python 3.11+ (web export, separate from the native pin)
- Export command: `python scripts/export_yolo26n.py --format onnx --weights yolo26n.pt --output-dir public/models --force`
- Expected input shape: `(1, 3, 640, 640)`
- Expected output shape: `(1, 300, 6)`

Example local export:

```bash
python -m pip install ultralytics==8.4.112 onnx
python scripts/export_yolo26n.py --format onnx --weights yolo26n.pt --output-dir public/models --force
```

Preserve the model-operations guidance in [docs/yolo26-model-ops.md](docs/yolo26-model-ops.md). The native first-use verified model cache is not a replacement for this browser export step. Do not commit model weights or private footage. The source repository is [AGPL-3.0-or-later](LICENSE); review the separate Ultralytics model/tooling terms and dependency notices in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before integration or redistribution.
