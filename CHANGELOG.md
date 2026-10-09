# Changelog

## v1.2.0-rc.1 - Native Preview (Pending Publication)

Evaluation prerelease targeting macOS 14+ on Apple Silicon arm64 and Windows 10/11 x64. Public release/download and final-artifact verification are not yet confirmed; this entry does not assert their completion.

- Shared Python/PySide6/OpenCV native UI for camera and local recorded-file monitoring; Mac MPS and Windows CPU inference.
- Real-speed recorded-video looping with asynchronous inference, fullscreen compact controls, reset and draggable zone points.
- `yolo26n-seg.pt` with `ultralytics==8.4.146` for segmentation-based close-range zone contact. Browser YOLO26n ONNX/WASM geometry/foot-point checks remain separate, without segmentation parity.
- Per-person breach events, locally persisted SQLite session data and five-sheet Excel exports: Records, Person Breaches, Aggregated Results, Overall Metrics, Session Metadata.
- No committed or packaged model weights. Implemented runtime cache downloads approved `yolo26n-seg.pt`/`yolo26n.pt` from official Ultralytics `v8.4.0` assets, verifies pinned SHA-256 digests and installs atomically into `~/Library/Caches/redzone-ai-monitor/models` on Mac or `%LOCALAPPDATA%\DROPS Red Zone Monitoring\models` on Windows for cached offline reuse.
- Model readiness feedback: Downloading AI model, Loading AI model, AI Ready, or failure with tooltip details.
- Expected assets: `DROPS-Red-Zone-Monitoring-macos-arm64.dmg`, `DROPS-Red-Zone-Monitoring-Windows-x64.zip`, `SHA256SUMS.txt`, `build-manifest.json`.
- Maintainer-reported verification: 49 assembled Python tests passed, plus the source self-test with actual model loading/inference on Mac MPS using Ultralytics 8.4.146. This does not establish packaged-download or site/hardware acceptance.
- Developer ID signing when available; preview is not Apple-notarized. Windows preview is unsigned and may trigger SmartScreen; Windows hardware validation is not claimed. Intel Macs and Windows ARM are unsupported and untested.
- Public AGPL evaluation preview with exact-tag corresponding application/build source, upstream licence/source references and dynamic Qt library replacement/rebuild/re-sign instructions. Licensing suitability for production/operational deployment remains an external gate, separate from this preview; no blanket compliance certificate is given.

See [the exact preview release](https://github.com/dropsforum/redzone-ai-monitor/releases/tag/v1.2.0-rc.1) and [desktop release guide](docs/desktop-releases.md). Links are publication destinations, not verified-live downloads yet.

## v1.1.0 - December 2025

Older stable release; not the current native preview. See its [historical release notes](https://github.com/dropsforum/redzone-ai-monitor/releases/tag/v1.1.0). No retrospective feature or test claims are added here.
