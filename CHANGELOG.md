# Exposure Zone Monitoring - Changelog

## v1.2.0-rc.1 - Native Preview

Evaluation prerelease targeting macOS 14+ on Apple Silicon arm64 and Windows 10/11 x64. Consult the exact release notes/build manifest for artifact verification and remaining limitations; this is not a validated operational safety control.

- Renamed the product to **Exposure Zone Monitoring** and removed prominent model-brand promotional wording while retaining technical model/version and licence details. Mac app: `Exposure Zone Monitoring.app`; Windows executable: `ExposureZoneMonitoring.exe` inside the `Exposure Zone Monitoring` folder.
- Added the exposure-avoidance-first philosophy, official article/working-draft references, DROPS Asia/DROPS Forum roles and implementation-support contact. Workshops and planning support do not confer accreditation, enforce access or transfer site accountability.
- Kept `dropsforum/redzone-ai-monitor`, the preview tag and legacy session/model-cache folders unchanged intentionally for compatibility and history continuity. Web branding changes are source changes, not a confirmed Vercel deployment.

- Shared Python/PySide6/OpenCV native UI for camera and local recorded-file monitoring; Mac MPS and Windows CPU inference.
- Real-speed recorded-video looping with asynchronous inference, fullscreen compact controls, reset and draggable zone points.
- `yolo26n-seg.pt` with `ultralytics==8.4.146` for segmentation-based close-range zone contact. Browser YOLO26n ONNX/WASM geometry/foot-point checks remain separate, without segmentation parity.
- Per-person breach events, locally persisted SQLite session data and five-sheet Excel exports: Records, Person Breaches, Aggregated Results, Overall Metrics, Session Metadata.
- No committed or packaged model weights. Implemented runtime cache downloads approved `yolo26n-seg.pt`/`yolo26n.pt` from official Ultralytics `v8.4.0` assets, verifies pinned SHA-256 digests and installs atomically into `~/Library/Caches/redzone-ai-monitor/models` on Mac or `%LOCALAPPDATA%\DROPS Red Zone Monitoring\models` on Windows for cached offline reuse.
- Model readiness feedback: Downloading AI model, Loading AI model, AI Ready, or failure with tooltip details.
- Expected assets: `Exposure-Zone-Monitoring-macos-arm64.dmg`, `Exposure-Zone-Monitoring-Windows-x64.zip`, `SHA256SUMS.txt`, `build-manifest.json`.
- Maintainer-reported verification: 59 assembled Python tests passed, plus Mac self-tests with actual model loading/inference on MPS using Ultralytics 8.4.146. Automated checks do not establish final renamed-build/public-download verification or site/hardware acceptance.
- Developer ID signing when available; preview is not Apple-notarized. Windows preview is unsigned and may trigger SmartScreen; Windows hardware validation is not claimed. Intel Macs and Windows ARM are unsupported and untested.
- Public AGPL evaluation preview with exact-tag corresponding application/build source, upstream licence/source references and dynamic Qt library replacement/rebuild/re-sign instructions. Licensing suitability for production/operational deployment remains an external gate, separate from this preview; no blanket compliance certificate is given.
- Packaging includes full GNU AGPL/GPL/LGPL texts explicitly rather than relying on Qt wheel licence contents; final artifact inclusion remains a maintainer verification item.

See [the exact preview release](https://github.com/dropsforum/redzone-ai-monitor/releases/tag/v1.2.0-rc.1) and [desktop release guide](docs/desktop-releases.md).

## v1.1.0 - December 2025

Older stable release; not the current native preview. See its [historical release notes](https://github.com/dropsforum/redzone-ai-monitor/releases/tag/v1.1.0). No retrospective feature or test claims are added here.
