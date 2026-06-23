# DROPS Red Zone Monitoring

DROPS Red Zone Monitoring is a prototype application exploring how local AI and computer vision can support Exposure Zone Management.

The project is based on a simple principle: monitoring should help organizations challenge access, not merely administer it. A person entering a red zone, restricted access zone, or other line-of-fire exposure area should not be treated as normal simply because entry can be detected, alarmed, or recorded. The stronger question is whether the work could have been designed so that entry was avoided, reduced, shortened, delayed, or better controlled in the first place.

This app is therefore not intended to make entry into hazardous areas acceptable. It is intended to help teams verify whether controls are working, detect unauthorized or unexpected presence, and identify exposure patterns that should trigger learning and improvement.

In the context of DROPS Exposure Zone Management, AI monitoring can support assurance by helping teams see where exposure occurs, whether access rules are being followed, and where repeated entry may indicate a deeper planning or design issue. The goal is not better permission to enter danger. The goal is better evidence to reduce the need for entry.

This repository contains two DROPS Red Zone Monitoring targets:

- **Web app**: a Next.js browser proof of concept that runs YOLO26 with ONNX Runtime Web.
- **Mac desktop app**: a high-performance native Python/OpenCV/Ultralytics app packaged with PyInstaller.

## 🚀 Getting Started

### Prerequisites

- Node.js (Latest LTS recommended)
- npm (comes with Node.js)

### Local Setup

1.  **Install dependencies**:
    ```bash
    npm install
    ```

2.  **Start the development server**:
    ```bash
    npm run dev
    ```

3.  **Access the app**:
    Open [http://localhost:3000](http://localhost:3000) in your browser.
    *Note: If port 3000 is in use, Next.js will automatically try 3001, 3002, etc.*

## 🌐 Deployment (Vercel)

This project is optimized for deployment on Vercel.

**Note on Build**: Due to custom Webpack configurations required for ONNX Runtime Web, you must ensure the build command uses the `--webpack` flag:
- **Build Command**: `npm run build` (which is mapped to `next build --webpack` in `package.json`)
- **Framework Preset**: Next.js
- **Node.js Version**: 20.x or 22.x

## macOS Native App

The Mac version intentionally does not use Tauri or Electron. It uses the faster Python/OpenCV/Ultralytics path and packages that as a signed `.app`.

### Run locally

```bash
python3.11 -m venv .venv-mac
source .venv-mac/bin/activate
python -m pip install -r requirements_ai.txt
python run_ai_app.py
```

Use a recorded video:

```bash
python run_ai_app.py --video "/path/to/video.mp4"
```

Recorded videos stay paused until you press `S` to start monitoring, then they play at normal video speed and loop. YOLO inference runs asynchronously so playback is not tied to AI throughput.

### Build the signed Mac app

```bash
npm run mac:native:build
npm run mac:native:dmg
```

Set `MACOS_CODESIGN_IDENTITY` to a local Developer ID identity before building if you want the `.app` and `.dmg` signed. Notarization is prepared but requires Apple credentials:

```bash
MACOS_CODESIGN_IDENTITY="Developer ID Application: Your Organization (TEAMID)" npm run mac:native:build
APPLE_NOTARY_PROFILE="profile-name" npm run mac:native:notarize
```

The app bundle includes `NSCameraUsageDescription` and the camera entitlement in `packaging/macos/Entitlements.plist`.

## Intended Use

This prototype is intended for demonstration, learning, and evaluation. It may help illustrate how computer vision, configurable zones, local inference, and visual alerts can support exposure-zone discussions.

It should not be used as the only control for hazardous work. Any operational use would require site-specific risk assessment, validation, governance, privacy review, human response arrangements, and integration with existing permit, authorization, and stop-work processes.

## 📦 Features

- **Real-time AI Detection**: Runs YOLO26 directly in your browser using ONNX Runtime Web.
- **Recorded Video Mode**: Analyze a local recorded video file in the browser without uploading it.
- **Native Mac Desktop Path**: Runs Ultralytics YOLO26 through Python/OpenCV for higher local inference performance.
- **Custom Zones**: Draw and edit monitoring zones directly on the live camera feed.
- **Visual Alerts**: On-screen indicators and sound alerts when someone enters a "Red Zone".
- **Privacy First**: All processing happens locally on your device. No video data is sent to any server.

## Design Principles

- **Challenge access first**: monitoring should support the question of whether entry is necessary.
- **Assure controls**: detections and alerts should help verify whether access controls are working.
- **Learn from patterns**: repeated or normalized entry should trigger review of the work method.
- **Keep processing local**: video analysis is designed to run on the user's device.
- **Do not normalize exposure**: technology should help reduce exposure, not justify it.

## 🛠 Project Structure

- `src/components`: UI components (video source, Zone Editor, Overlays).
- `src/lib`: Core logic (YOLO detector, zone checking, alert management).
- `public/models`: Local model output directory. Model binaries are intentionally not committed.
- `public/wasm`: WebAssembly files for ONNX Runtime.

## AI Model & Runtime Provenance

- Model file: `public/models/yolo26n.onnx`
- Source model: `yolo26n.pt` from Ultralytics assets, downloaded/exported locally by each user
- Model binaries: intentionally excluded from this public repository
- Export toolchain: `ultralytics==8.4.68`, `onnx==1.20.0`, Python 3.12
- Export command: `YOLO("yolo26n.pt").export(format="onnx", imgsz=640, opset=17, simplify=False)`
- Expected input shape: `(1, 3, 640, 640)`
- Expected output shape: `(1, 300, 6)`
- Browser runtime: `onnxruntime-web@1.26.0`; files in `public/wasm` are copied from `node_modules/onnxruntime-web/dist`.

Generate the browser model locally before running detection:

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

Ultralytics models and tooling have their own license terms. Users are responsible for confirming that their intended use, especially production or commercial deployment, complies with those terms.

## 📄 Integration & Documentation

For instructions on integrating this module into the `dropsforum.org` website, see [PACKAGE_README.md](./PACKAGE_README.md).

---
*DROPS FORUM Red Zone Monitoring POC*
