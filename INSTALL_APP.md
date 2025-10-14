# Install: DROPS Red Zone Monitoring POC (macOS, Apple Silicon)

This preview build is unsigned. On first run, use Right‑click → Open to bypass Gatekeeper.

## Build (developer machine)
1. Activate your venv and install packager:
```bash
pip install pyinstaller
```
2. Build the .app:
```bash
pyinstaller packaging/macos/pyinstaller.spec
```
3. The app will be at `dist/DROPS Red Zone Monitoring POC.app`.

## Run on another Mac (M1–M3)
1. Copy the `.app` to Applications.
2. First run:
   - Right‑click the app → Open → Open
   - Grant Camera permission when prompted
3. Controls:
   - D draw zone, Enter close, C clear
   - S start monitoring, P pause, Q quit
   - M switch camera

## Optional: Create DMG for sharing
```bash
hdiutil create -volname DROPS-POC -srcfolder dist/"DROPS Red Zone Monitoring POC.app" -ov -format UDZO DROPS-POC-macos-arm64.dmg
```

