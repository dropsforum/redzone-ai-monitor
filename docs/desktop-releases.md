# Exposure Zone Monitoring - Native Desktop Preview

## Release Status

Preview: **Exposure Zone Monitoring v1.2.0-rc.1** in the public `dropsforum/redzone-ai-monitor` repository. This is a prerelease for demonstration, learning and evaluation, not a validated operational safety control. Consult the exact release notes/build manifest for artifact verification and remaining limitations. Website source branding changes do not imply a Vercel deployment.

The older stable **v1.1.0 (December 2025)** is not this native preview. Use the exact tag rather than GitHub's latest-stable shortcut.

| Item | Exact preview URL |
| --- | --- |
| Release notes | [v1.2.0-rc.1](https://github.com/dropsforum/redzone-ai-monitor/releases/tag/v1.2.0-rc.1) |
| macOS 14+ Apple Silicon arm64 | [Exposure-Zone-Monitoring-macos-arm64.dmg](https://github.com/dropsforum/redzone-ai-monitor/releases/download/v1.2.0-rc.1/Exposure-Zone-Monitoring-macos-arm64.dmg) |
| Windows 10/11 x64 | [Exposure-Zone-Monitoring-Windows-x64.zip](https://github.com/dropsforum/redzone-ai-monitor/releases/download/v1.2.0-rc.1/Exposure-Zone-Monitoring-Windows-x64.zip) |
| Download checksums | [SHA256SUMS.txt](https://github.com/dropsforum/redzone-ai-monitor/releases/download/v1.2.0-rc.1/SHA256SUMS.txt) |
| Build provenance | [build-manifest.json](https://github.com/dropsforum/redzone-ai-monitor/releases/download/v1.2.0-rc.1/build-manifest.json) |

## Installation

Packaged binaries include the runtime: **no separate Python installation is needed**. Source development is optional and described in [README.md](../README.md).

- **Mac:** macOS 14 or later, Apple Silicon arm64 only. The pinned PyTorch 2.12 wheel and app's `LSMinimumSystemVersion` have a macOS 14 deployment floor. Open the DMG, copy **Exposure Zone Monitoring.app** to Applications, then launch it. Developer ID signing is used when available; this preview is **not Apple-notarized**. Check the release notes for the actual signing identity. Gatekeeper may warn; verify provenance and follow local security policy.
- **Windows:** Windows 10/11 x64 only. Extract the entire ZIP into a writable location, retain the **Exposure Zone Monitoring** folder and its bundled libraries, then launch **ExposureZoneMonitoring.exe** inside that folder. This preview is unsigned; SmartScreen may warn. Do not disable security controls to install it. Use your organization's approved evaluation procedure.
- **Excluded:** Intel Macs and Windows ARM are unsupported and untested. A Windows build or CI pass is not Windows hardware testing; no camera, performance or hardware-validation claim is made here.

Download the checksum file from the same exact tag and compare the relevant asset's digest before opening it:

```bash
# macOS, in the download directory
shasum -a 256 Exposure-Zone-Monitoring-macos-arm64.dmg
```

```powershell
# Windows PowerShell, in the download directory
Get-FileHash .\Exposure-Zone-Monitoring-Windows-x64.zip -Algorithm SHA256
```

Compare the result to that filename's entry in `SHA256SUMS.txt`. Stop if it differs. A checksum detects a changed download; it does not replace code-signing trust, licence review or safety validation. Inspect `build-manifest.json` and release notes for the actual source revision, platform, dependency and verification evidence; do not infer these from the filename alone.

## First Use and Models

Model weights are **not committed or packaged**. The implemented runtime in `ai_motion_app/model_cache.py` downloads the selected approved model from official [Ultralytics v8.4.0 assets](https://github.com/ultralytics/assets/releases/tag/v8.4.0), verifies the pinned SHA-256, then atomically moves the completed file into its cache. Existing cached files are hash-checked before reuse. See the verification scope and maintainer checklist below for checks that apply to each final artifact.

Default cache directories (separate from the session database):

- Mac: `~/Library/Caches/redzone-ai-monitor/models`
- Windows: `%LOCALAPPDATA%\DROPS Red Zone Monitoring\models`

These cache names are intentionally unchanged for compatibility. Do not rename them to match Exposure Zone Monitoring; the product rename preserves existing cached models and monitoring history.

| Approved model | Pinned SHA-256 |
| --- | --- |
| `yolo26n-seg.pt` (native default) | `361fbfabab285c3237700b6bb91d7ecfa602cd945fffda8dbe1242829b71e73f` |
| `yolo26n.pt` (detection option, not segmentation) | `9b09cc8bf347f0fc8a5f7657480587f25db09b34bf33b0652110fb03a8ad4fef` |

The source URL prefix is `https://github.com/ultralytics/assets/releases/download/v8.4.0/`. Model status shows **Downloading AI model**, then **Loading AI model**, then **AI Ready**, or a failure with details in the tooltip. Do not treat downloading, loading or failure as proof of no breach.

Internet access is required for the initial download. After verification, the cached model supports offline inference. An absent or invalid model must not be interpreted as a clear/no-breach result. If setup fails, check the error and connectivity; do not substitute arbitrary weights or bypass hash verification. Downloading weights separately does not avoid Ultralytics licensing obligations.

Native dependencies include `ultralytics==8.4.146`; default model is `yolo26n-seg.pt`. Mac uses PyTorch/MPS; Windows uses CPU. The browser remains YOLO26n ONNX/WASM detection with different geometry and foot-point logic, **not segmentation parity**. Do not use native evaluation to certify browser results.

## Monitoring and Reports

1. Select a camera or local recorded file. Allow camera access only when authorized; keep privacy and worker-monitoring policy in view.
2. Use ZONE to edit the zone by dragging its points, then SAVE to finish. RESET stops monitoring and clears the zone; FULL opens fullscreen with compact controls.
3. Use **START** in the Qt UI. Recorded files begin then, play at real speed and loop; asynchronous inference may sample fewer frames than playback. **STOP** ends monitoring. `S` is only a legacy OpenCV keyboard command (`--legacy-opencv`), not the Qt instruction.
4. Review segmentation-based close-range contact, per-person breaches and session records against representative footage. Occlusion, viewpoint, lighting, tracking loss and geometry can produce missed or false events. A track ID does not establish a person's identity.
5. Export the Excel workbook as needed. It has five sheets: **Records**, **Person Breaches**, **Aggregated Results**, **Overall Metrics**, **Session Metadata**. Reports describe observed detections, not complete exposure histories or proof of safety.

## Local Data and Privacy

The native app processes footage locally, does not upload video and does not automatically retain raw footage. First-use model retrieval contacts the upstream asset host but does not upload footage. Breach events and session metadata persist in a local SQLite database:

- Mac: `~/Library/Application Support/DROPS Red Zone Monitoring/monitoring.sqlite3`
- Windows: `%LOCALAPPDATA%\DROPS Red Zone Monitoring\monitoring.sqlite3`

The legacy **DROPS Red Zone Monitoring** storage folders are intentionally retained for compatibility and session-history continuity. They are not renamed or migrated by the product rename. The source repository and Mac `redzone-ai-monitor` cache identifier also remain unchanged.

Exports are saved to the path you select. Database records and reports can be sensitive even without images. Define access, retention, lawful basis/consent, worker communication and deletion procedures before evaluation. Do not assume uninstalling the app deletes user data or exported reports. Local processing is not a blanket privacy-compliance guarantee.

Monitoring should challenge the need for entry, not normalize line-of-fire exposure. Operational use requires site-specific risk assessment, camera/zone validation, privacy review, human response, authorization and stop-work arrangements. Never rely on this prototype as the only control for hazardous work.

## Verification Scope

The maintainer reports **59 assembled Python tests passed** and successful **Mac self-tests with actual model loading/inference on MPS**, using Ultralytics **8.4.146**. The self-test exercises recorded-video playback, Qt rendering/zone dragging, contact-state logic, SQLite persistence, five-sheet export and model inference. It uses generated footage, not a physical camera or a representative site trial. Final renamed-build and public-download evidence belongs to the release notes/build manifest after verification. Automated checks do not establish Windows hardware validation or operational safety acceptance.

For reproducibility in the development environment:

```bash
python -m unittest discover -s tests/python -p 'test_*.py'
python run_ai_app.py --self-test --self-test-output /tmp/redzone-source-self-test.json --device mps
```

The test count belongs to the reported assembled revision; future revisions may change it. Final artifact reports and download verification belong in the exact release notes/build evidence.

## Replacing Qt Libraries and Rebuilding

The native app uses PyInstaller **onedir** packaging with dynamically linked PySide6/Qt libraries, not statically embedded Qt. Recipients may replace compatible libraries or rebuild with modified libraries under the applicable terms. Obtain corresponding application/build source from the [exact release tag](https://github.com/dropsforum/redzone-ai-monitor/tree/v1.2.0-rc.1), alongside [upstream licence/source references](../THIRD_PARTY_NOTICES.md).

1. Obtain the tagged source in a separate development checkout, not over an existing installation:

```bash
git clone --branch v1.2.0-rc.1 https://github.com/dropsforum/redzone-ai-monitor.git redzone-preview-source
cd redzone-preview-source
```

2. Create the platform's Python 3.11 environment and install its requirements as described in [README.md](../README.md). Obtain the matching Qt/PySide6/Shiboken source from the official references in the notices; build compatible replacement wheels following [Qt for Python build instructions](https://doc.qt.io/qtforpython-6/building_from_source/index.html). Keep architecture and Python/Qt ABI compatible and replace dependent libraries/plugins consistently.
3. After dependency installation, install your replacement wheels into that environment using `python -m pip install --force-reinstall --no-deps /path/to/your/replacement.whl` for each wheel. Run `python -m pip check`. Do not rerun the dependency-installing build wrapper afterward, as it could restore the original pinned wheels. Build directly from the spec:

```bash
# On Mac, from the tagged repository root with the modified environment active
python -m PyInstaller packaging/macos/pyinstaller.spec --clean --noconfirm
```

```powershell
# On Windows x64, with the modified environment active
python -m PyInstaller packaging/windows/pyinstaller.spec --clean --noconfirm
```

The renamed outputs are `dist/Exposure Zone Monitoring.app` on Mac and `dist/Exposure Zone Monitoring/ExposureZoneMonitoring.exe` on Windows. For direct replacement in a copy of the onedir installation, locate the bundled PySide6/Qt libraries under the Mac app's `Contents/Frameworks` or the Windows folder's `_internal`; replace the matching libraries and plugins as a consistent set. Prefer the rebuild route when layout or ABI differs.

4. Changing a Mac bundle invalidates the distributor's signature. Sign your personal rebuilt/replaced copy with your own identity, or use an ad-hoc signature for local evaluation:

```bash
codesign --force --deep --sign - \
  --entitlements packaging/macos/Entitlements.plist \
  "dist/Exposure Zone Monitoring.app"
codesign --verify --deep --strict --verbose=2 "dist/Exposure Zone Monitoring.app"
```

For your own Developer ID identity, replace `--sign -` with `--sign "Developer ID Application: Your Organization (TEAMID)"` and add `--options runtime`. Ad-hoc signing is not Developer ID signing, notarization or a Gatekeeper approval. You do not need the distributor's signing key; follow your local installation/security policy and do not disable system protections. The Windows preview has no distributor signature to preserve.
5. Test the modified app and retain the corresponding source, licences and modification records if redistributing. Modified builds are not the publisher's original artifacts. These instructions explain the replacement/rebuild route; they do not certify every possible replacement or distribution as compliant.

## Maintainer Release Checklist

These are required review items, not completed claims:

- For the requested public AGPL evaluation preview, distribute the exact-tag corresponding application/build source, upstream licence/source references, required notices and Qt shared-library replacement/rebuild information for the actual binaries. Review the [dependency obligations](../THIRD_PARTY_NOTICES.md); this is not a compliance certificate. Keep the external licensing decision for production/operational deployment separate from preview publication.
- Build from the agreed source revision; inspect both artifacts to confirm no model weights, private footage, secrets or local session databases are included.
- Verify product/window titles, `Exposure Zone Monitoring.app`, Windows `ExposureZoneMonitoring.exe` inside the spaced product folder, and both renamed asset filenames. Preserve the legacy session/cache directories; verify existing-history continuity. Keep model names/version/provenance/licensing in technical documentation, not promotional banners.
- Verify that full GNU AGPL/GPL/LGPL texts and required dependency notices/source references are included in both final artifacts; do not rely on Qt wheels to carry all licence texts.
- Verify first-use official download and pinned SHA-256 rejection, OS cache persistence and offline reuse on each target.
- Verify installation, startup, camera/file selection, playback/looping, zone dragging/reset, fullscreen controls, segmentation contact, per-person/session persistence and all five Excel sheets. Record environment and observed results separately from expected behavior.
- Record actual Mac Developer ID signing and any separately proven notarization. State Windows unsigned status and hardware-test limitations explicitly.
- Generate and verify checksums and build provenance; publish the exact `v1.2.0-rc.1` tag as a prerelease with all four named assets. Test public release/download URLs after publication.
- Update pending statements only when the coordinator has evidence. A successful build, upload, public download and hardware validation are separate states.
