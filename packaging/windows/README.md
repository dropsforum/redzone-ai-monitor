# Exposure Zone Monitoring - Windows x64 Preview

Version: 1.2.0-rc.1 for Windows 10/11 x64, with CPU inference.
This public preview is for demonstration, learning and evaluation, not a
validated operational safety control. Windows ARM is not supported.

## Install and Start

Download the Windows ZIP and checksums from the exact
[v1.2.0-rc.1 release](https://github.com/dropsforum/redzone-ai-monitor/releases/tag/v1.2.0-rc.1).
Compare the ZIP's SHA256 with its entry in the release's `SHA256SUMS.txt`:

```powershell
Get-FileHash .\Exposure-Zone-Monitoring-Windows-x64.zip -Algorithm SHA256
```

Stop if the digest differs. Consult the release notes for the actual build
and verification evidence; a checksum does not establish publisher trust.

Extract the entire ZIP to a writable folder, then open
`Exposure Zone Monitoring/ExposureZoneMonitoring.exe`. Keep `_internal`
and all bundled DLLs beside the executable. No Python installation is required.
This preview is unsigned; Windows may display an unknown-publisher warning.
Never bypass your organization's application approval requirements.

## First Use

Model weights are not included. The application downloads its approved
`yolo26n-seg.pt` model on first use and verifies its pinned SHA256 before
caching it in `%LOCALAPPDATA%\DROPS Red Zone Monitoring\models`.
Internet access is required for the first download; a verified cached model
can be reused offline. Wait for **AI Ready** before evaluating detections.
If loading fails, inspect the error tooltip and connectivity. Do not bypass
hash verification or treat a failed model as a clear/no-breach result.

Select a camera or recorded file, use **ZONE** to position the zone corners,
then **SAVE** and **START**. **STOP** ends monitoring. Authorize camera access
only under your evaluation and privacy policy.

No user configurations, recordings, logs or session databases are shipped.
Session records are stored locally in
`%LOCALAPPDATA%\DROPS Red Zone Monitoring\monitoring.sqlite3`; exported reports
are saved where you choose. Removing the extracted application does not
remove those records, cached models or exports.
The legacy cache/data folder name is retained for compatibility with earlier
previews; the product is now Exposure Zone Monitoring.

See [the desktop guide](docs/desktop-releases.md) for installation, cache,
monitoring, reports, privacy and source/library guidance, and
[model operations](docs/yolo26-model-ops.md) for model details.

This monitoring preview is not a certified safety system and does not replace
physical barriers, authorized access controls or human supervision. Detection
can miss people; use approved exposure-management procedures.

## Diagnostics and Source

To run the hardware-free diagnostic from the extracted application folder:

```powershell
$app = Start-Process -FilePath '.\ExposureZoneMonitoring.exe' -ArgumentList '--self-test', '--self-test-output', 'self-test.json' -Wait -PassThru
$app.ExitCode
Get-Content .\self-test.json
```

Success requires exit code zero and JSON `success: true`. Initial model
retrieval may require internet access. This diagnostic does not validate a
physical camera, site conditions or safety performance.

The application source is public under the existing AGPL-3.0-or-later licence
in [dropsforum/redzone-ai-monitor](https://github.com/dropsforum/redzone-ai-monitor).
Use the source revision identified by the preview's build manifest when
rebuilding. Exact installed dependency versions are recorded in
`docs/build-dependencies.json`; Windows requirements are included in
`docs/requirements_windows.txt`. Source packaging scripts are in
`packaging/windows` in the repository.

Shared libraries remain separate under `_internal`. Keep a backup before
replacing libraries, use compatible Windows x64 builds and retain the expected
paths and DLL names. Rebuilding from source is an alternative to in-place
replacement. Consult [the canonical dependency notices](THIRD_PARTY_NOTICES.md)
and bundled `licenses/` for applicable terms and source/replacement obligations.
Production licensing and operational approval are separate external gates;
this release is explicitly a public preview, not production approval.
