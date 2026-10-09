# DROPS Red Zone Monitoring

DROPS Red Zone Monitoring is a prototype application exploring how local AI and computer vision can support Exposure Zone Management.

The project is based on a simple principle: monitoring should help organizations challenge access, not merely administer it. A person entering a red zone, restricted access zone, or other line-of-fire exposure area should not be treated as normal simply because entry can be detected, alarmed, or recorded. The stronger question is whether the work could have been designed so that entry was avoided, reduced, shortened, delayed, or better controlled in the first place.

This app is therefore not intended to make entry into hazardous areas acceptable. It is intended to help teams verify whether controls are working, detect unauthorized or unexpected presence, and identify exposure patterns that should trigger learning and improvement.

In the context of DROPS Exposure Zone Management, AI monitoring can support assurance by helping teams see where exposure occurs, whether access rules are being followed, and where repeated entry may indicate a deeper planning or design issue. The goal is not better permission to enter danger. The goal is better evidence to reduce the need for entry.

This repository contains two DROPS Red Zone Monitoring targets:

- **Native desktop app**: Python/PySide6/OpenCV/Ultralytics, packaged with PyInstaller for macOS 14+ on Apple Silicon arm64 (MPS inference) and Windows 10/11 x64 (CPU inference).
- **Web app**: a Next.js browser proof of concept using YOLO26n detection with ONNX Runtime Web/WASM. Its zone geometry and foot-point checks differ from native segmentation; it does not have segmentation parity.

## Native Preview Downloads

Preview **v1.2.0-rc.1** is for demonstration and evaluation only. Public-download availability is not yet confirmed; check the exact release notes for publication status and verification evidence. These links identify the preview, not the older stable release:

- [Preview release and verification notes](https://github.com/dropsforum/redzone-ai-monitor/releases/tag/v1.2.0-rc.1)
- [Mac download: DROPS-Red-Zone-Monitoring-macos-arm64.dmg](https://github.com/dropsforum/redzone-ai-monitor/releases/download/v1.2.0-rc.1/DROPS-Red-Zone-Monitoring-macos-arm64.dmg)
- [Windows download: DROPS-Red-Zone-Monitoring-Windows-x64.zip](https://github.com/dropsforum/redzone-ai-monitor/releases/download/v1.2.0-rc.1/DROPS-Red-Zone-Monitoring-Windows-x64.zip)
- [SHA256SUMS.txt](https://github.com/dropsforum/redzone-ai-monitor/releases/download/v1.2.0-rc.1/SHA256SUMS.txt)
- [build-manifest.json](https://github.com/dropsforum/redzone-ai-monitor/releases/download/v1.2.0-rc.1/build-manifest.json)

Use the preview tag above: GitHub's latest stable release remains the older **v1.1.0 (December 2025)** and is not this native preview. Packaged apps require no separate Python installation. Intel Macs and Windows ARM are unsupported and untested for this release; Windows hardware validation is not claimed.

On Mac, open the DMG and copy the app to Applications. Developer ID signing is used when an identity is available; this preview is **not Apple-notarized**. On Windows, extract the entire ZIP before launching its app executable; keep its bundled libraries alongside it. The Windows preview is unsigned and may trigger SmartScreen. Confirm the source and checksum and follow your organization's security policy; do not disable protections.

Model weights are not committed or packaged. On first use, the native app downloads the selected approved model (`yolo26n-seg.pt` by default, or `yolo26n.pt` detection) from official Ultralytics `v8.4.0` assets and verifies its pinned SHA-256 before an atomic move into the user cache. Mac cache: `~/Library/Caches/redzone-ai-monitor/models`; Windows cache: `%LOCALAPPDATA%\DROPS Red Zone Monitoring\models`. Internet is needed initially; a verified cached model can subsequently run offline. See [desktop release instructions](docs/desktop-releases.md) for checksums, readiness messages, local records and the scope of verification.

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

## Native Desktop App

The native app uses the same PySide6 UI on Mac and Windows, not Tauri or Electron. It supports camera and recorded-file sources, real-speed looping playback, fullscreen with compact controls, reset, draggable zone points, segmentation-based close-range zone contact, per-person breach events, session persistence and a five-sheet Excel report. Detection and tracking are fallible: a track ID is not a verified personal identity, and a clear frame is not proof that an area is safe.

Native model: `yolo26n-seg.pt`, with `ultralytics==8.4.146`. Mac uses PyTorch/MPS; the Windows preview uses CPU. Performance depends on the device, source and scene; no Windows hardware performance result is asserted.

Maintainer-reported Mac verification: **49 assembled Python tests passed**, and the source self-test passed with actual model loading and inference on **MPS**, using Ultralytics **8.4.146**. These results do not establish packaged-download verification, Windows hardware validation or operational safety acceptance.

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

In the default Qt UI, select a camera or recorded file and use **START** to begin monitoring. Recorded videos stay paused until START, then play at normal video speed and loop. YOLO inference runs asynchronously so playback is not tied to AI throughput. Use ZONE to edit draggable points and SAVE to finish; RESET stops monitoring and clears the zone, and FULL opens fullscreen with compact controls. The `S` keyboard instruction applies only to the legacy OpenCV UI launched with `--legacy-opencv`, not the Qt preview.

Model status progresses through **Downloading AI model**, **Loading AI model** and **AI Ready**, or shows a failure with details in its tooltip. Wait for AI Ready; download/loading/failure is not a no-breach result.

For Windows source development (not needed for the packaged ZIP):

```powershell
py -3.11 -m venv .venv-win
.\.venv-win\Scripts\Activate.ps1
python -m pip install --only-binary=:all: torch==2.12.0+cpu torchvision==0.27.0+cpu --index-url https://download.pytorch.org/whl/cpu
python -m pip install --only-binary=:all: -r requirements_windows.txt
python run_ai_app.py --device cpu
```

The default Mac backend is PyTorch/MPS. To benchmark the experimental
CoreML FP16 export without changing the default:

```bash
python run_ai_app.py \
  --backend coreml \
  --model ~/Library/Caches/redzone-ai-monitor/yolo26n-exports/yolo26n.mlpackage
```

### Build the Mac app (developers)

```bash
npm run mac:native:build
npm run mac:native:dmg
```

Set `MACOS_CODESIGN_IDENTITY` to a local Developer ID identity before building if you want the `.app` and `.dmg` signed. Notarization is a separate, credential-dependent step; these commands do not establish that the preview has been notarized:

```bash
MACOS_CODESIGN_IDENTITY="Developer ID Application: Your Organization (TEAMID)" npm run mac:native:build
APPLE_NOTARY_PROFILE="profile-name" npm run mac:native:notarize
```

The app bundle includes `NSCameraUsageDescription` and the camera entitlement in `packaging/macos/Entitlements.plist`.

### Privacy and Local Records

Camera/file inference stays on the device. The app does not upload footage or automatically retain raw video. The initial model download is a network request, not a footage upload. Native breach and session data persist locally in `monitoring.sqlite3` under `~/Library/Application Support/DROPS Red Zone Monitoring/` on Mac or `%LOCALAPPDATA%\DROPS Red Zone Monitoring\` on Windows. Exported reports remain wherever you choose to save them.

The Excel workbook contains **Records**, **Person Breaches**, **Aggregated Results**, **Overall Metrics** and **Session Metadata**. Local records and exports may still be sensitive worker-monitoring data: agree camera permissions, access, retention, consent/legal basis and deletion procedures before site evaluation. Local processing alone does not establish privacy compliance.

## Intended Use

This prototype is intended for demonstration, learning, and evaluation. It may help illustrate how computer vision, configurable zones, local inference, and visual alerts can support exposure-zone discussions.

It should not be used as the only control for hazardous work. Any operational use would require site-specific risk assessment, validation, governance, privacy review, human response arrangements, and integration with existing permit, authorization, and stop-work processes.

## 📦 Features

- **Real-time AI Detection**: Runs YOLO26 directly in your browser using ONNX Runtime Web.
- **Recorded Video Mode**: Analyze a local recorded video file in the browser without uploading it.
- **Native Desktop Path**: Runs YOLO26n segmentation through Python/PySide6/OpenCV, with local session records and Excel export on Mac and Windows.
- **Custom Zones**: Draw and edit monitoring zones directly on the live camera feed.
- **Visual Alerts**: On-screen indicators and sound alerts when someone enters a "Red Zone".
- **Local Processing**: No footage upload or automatic raw-footage retention; native breach/session records are stored locally. Initial native model setup requires internet.

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

## Browser AI Model & Runtime Provenance

This section describes the web detection/export path, not the native `yolo26n-seg.pt` segmentation runtime. Browser foot-point zone checks and geometry must be validated separately; native results cannot establish browser parity.

- Model file: `public/models/yolo26n.onnx`
- Source model: `yolo26n.pt` from Ultralytics assets, downloaded/exported locally by each user
- Model binaries: intentionally excluded from this public repository
- Export toolchain: `ultralytics==8.4.112`, `onnx`, Python 3.11+
- Export command: `python scripts/export_yolo26n.py --format onnx --weights yolo26n.pt --output-dir public/models --force`
- Expected input shape: `(1, 3, 640, 640)`
- Expected output shape: `(1, 300, 6)`
- Browser runtime: `onnxruntime-web@1.26.0`; files in `public/wasm` are copied from `node_modules/onnxruntime-web/dist`.

The YOLO26 end-to-end output already contains final `xyxy`, confidence, and
class values, so the browser path must not apply a second NMS pass. LiteRT and
CoreML FP16 are experimental benchmark candidates. ONNX/WASM and PyTorch/MPS
remain the default paths until a representative-footage benchmark meets
the documented promotion thresholds.

Generate the browser model locally before running detection:

```bash
python -m pip install ultralytics==8.4.112 onnx
python scripts/export_yolo26n.py --format onnx --weights yolo26n.pt --output-dir public/models --force
```

Export the experimental formats and create SHA-256 provenance or benchmark
templates with the scripts documented in
[`docs/yolo26-model-ops.md`](./docs/yolo26-model-ops.md). Their default output
locations are outside the repository. The existing `.gitignore` excludes the
generated browser and Mac model artifacts; do not place provenance, benchmark
outputs, or private footage in tracked repository paths.

## Licensing

The repository is AGPL-3.0-or-later, as stated in [LICENSE](LICENSE). The public evaluation preview is distributed on that open-source basis, with corresponding application/build source at the [exact v1.2.0-rc.1 tag](https://github.com/dropsforum/redzone-ai-monitor/tree/v1.2.0-rc.1), upstream licence/source references and [Qt replacement/rebuild instructions](docs/desktop-releases.md#replacing-qt-libraries-and-rebuilding). Source-tag availability follows publication status above.

Ultralytics code and models have AGPL-3.0 and commercial licensing options; downloading weights separately does not remove their obligations. Licensing suitability for **production or operational deployment** remains an external decision for the intended use, separate from this requested public AGPL preview. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Neither this documentation nor the preview is a blanket compliance certificate, unrestricted commercial-use permission or a statement that every enterprise use requires a paid licence.

## 📄 Integration & Documentation

For instructions on integrating this module into the `dropsforum.org` website, see [PACKAGE_README.md](./PACKAGE_README.md).

For native installation and release verification, see [docs/desktop-releases.md](docs/desktop-releases.md); preview changes are recorded in [CHANGELOG.md](CHANGELOG.md).

---
*DROPS FORUM Red Zone Monitoring POC*
