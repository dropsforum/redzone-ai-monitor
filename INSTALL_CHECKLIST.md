# Installation Checklist

Use this checklist to track your installation progress.

## Pre-Installation

- [ ] macOS 10.15 or later
- [ ] Administrator access on Mac
- [ ] Camera connected and working
- [ ] Internet connection available
- [ ] At least 500MB free disk space

## Step 1: Install Homebrew

**Estimated time:** 5-10 minutes

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

- [ ] Homebrew installed
- [ ] Added to PATH (follow the instructions shown)
- [ ] Verify: Run `brew --version`

## Step 2: Install System Dependencies

**Estimated time:** 10-15 minutes

```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
chmod +x setup_dependencies.sh
./setup_dependencies.sh
```

Wait for completion. This will install:
- [ ] FFmpeg
- [ ] libmicrohttpd
- [ ] libjpeg
- [ ] Python dependencies
- [ ] Virtual environment created

Expected output: "✓ Dependencies installation complete!"

## Step 3: Build Motion

**Estimated time:** 5-10 minutes

```bash
chmod +x build_motion.sh
./build_motion.sh
```

Wait for compilation (may take several minutes on slower Macs)

- [ ] Motion repository cloned
- [ ] Configuration successful
- [ ] Build successful
- [ ] Installation successful

Expected output: "✓ Motion build complete!"

**If build fails**, check TROUBLESHOOTING.md

## Step 4: Create Configuration

**Estimated time:** 1 minute

```bash
source venv/bin/activate
python3 create_config.py
```

- [ ] Configuration created: `config/motion.conf`
- [ ] Event scripts created: `scripts/*.sh`
- [ ] Directories created

Expected output: "✓ Configuration setup complete!"

## Step 5: Test System

**Estimated time:** 2 minutes

```bash
python3 test_camera.py
```

Check each test result:
- [ ] ✓ Camera Devices
- [ ] ✓ Video Device Support
- [ ] ✓ Motion Build
- [ ] ✓ Motion Configuration
- [ ] ✓ Python Dependencies

Expected output: "✓ All checks passed!"

**If any checks fail**, review the error messages and consult TROUBLESHOOTING.md

## Step 6: Grant Permissions

- [ ] Open System Settings
- [ ] Go to Privacy & Security > Camera
- [ ] Enable camera for Terminal (or Python)
- [ ] (Optional) Enable notifications in System Settings > Notifications

## Step 7: First Run

**Estimated time:** 1 minute

```bash
./run_app.sh
```

or

```bash
python3 motion_app.py
```

- [ ] Application starts without errors
- [ ] Menu bar icon appears (💤)
- [ ] No error dialogs

**If menu bar icon doesn't appear**, check that you're running from a terminal with appropriate permissions.

## Step 8: Start Monitoring

- [ ] Click menu bar icon
- [ ] Click "Start Monitoring"
- [ ] Icon changes to 👁️
- [ ] No error messages

## Step 9: Verify Detection

- [ ] Click "View Camera Feed"
- [ ] Browser opens to http://localhost:8081
- [ ] Camera feed visible
- [ ] Wave hand in front of camera
- [ ] Notification appears
- [ ] Check captures folder for images

```bash
open captures/
```

- [ ] Images or videos saved

## Step 10: Configure Zone Detection (Optional)

**Estimated time:** 10 minutes

- [ ] View camera feed and take screenshot
- [ ] Open screenshot in image editor
- [ ] Create mask (white = detect, black = ignore)
- [ ] Save as `config/zones/mask.png`
- [ ] Edit `config/motion.conf`, uncomment `mask_file` line
- [ ] Restart monitoring
- [ ] Test zone detection

Or use the helper:
```bash
python3 create_zone_mask.py
```

## Step 11: Fine-Tune Settings (Optional)

Edit `config/motion.conf`:

- [ ] Adjust sensitivity (threshold)
- [ ] Set event gap
- [ ] Configure capture quality
- [ ] Set minimum motion frames
- [ ] Enable/disable video recording

Test after each change:
```bash
# Stop monitoring (click icon > Stop Monitoring)
# Edit config/motion.conf
# Start monitoring again
```

## Daily Usage Checklist

### Starting the App

- [ ] Open Terminal
- [ ] Navigate to project: `cd "/Volumes/Data Vault/Cursor 2/Motion"`
- [ ] Activate environment: `source venv/bin/activate`
- [ ] Run app: `python3 motion_app.py`
- [ ] Click icon > Start Monitoring

### Stopping the App

- [ ] Click icon > Stop Monitoring
- [ ] Click icon > Quit

### Checking Captures

- [ ] Click icon > Open Captures Folder

Or:
```bash
open captures/
```

### Viewing Logs

```bash
tail -f logs/motion.log
```

## Troubleshooting Quick Reference

| Problem | Quick Fix |
|---------|-----------|
| Camera not detected | Check connection, grant permissions |
| Motion won't start | Check `logs/motion.log`, verify config |
| No notifications | Enable in System Settings > Notifications |
| Port already in use | Change ports in `config/motion.conf` |
| Too sensitive | Increase `threshold` in config |
| Not sensitive enough | Decrease `threshold` in config |
| Menu bar icon missing | Grant accessibility permissions |

For detailed troubleshooting, see TROUBLESHOOTING.md

## Create Distribution Package (Optional)

**Estimated time:** 10 minutes

To create an installer for other Macs:

```bash
./create_installer.sh
```

- [ ] PyInstaller installed
- [ ] App bundled
- [ ] DMG created: `dist/MotionDetector-v1.0.0.dmg`
- [ ] PKG created: `dist/MotionDetector-v1.0.0.pkg`

## Verification Checklist

Before considering installation complete:

### Functional Tests
- [ ] App launches successfully
- [ ] Menu bar icon appears
- [ ] Monitoring starts
- [ ] Camera feed viewable
- [ ] Motion detected
- [ ] Notifications received
- [ ] Images saved to captures/
- [ ] Monitoring stops
- [ ] App quits cleanly

### Configuration Tests
- [ ] Config file exists and valid
- [ ] Event scripts execute
- [ ] Zone mask can be applied
- [ ] Settings changes take effect

### Performance Tests
- [ ] CPU usage reasonable (<30% typical)
- [ ] No memory leaks (stable over time)
- [ ] Notifications not overwhelming
- [ ] Captures not filling disk

## Installation Complete! 🎉

When all items are checked:
- ✅ Application is fully installed
- ✅ Camera detection is working
- ✅ Notifications are functional
- ✅ Ready for daily use

## Next Steps

1. **Review Documentation**
   - Read QUICKSTART.md for usage tips
   - Bookmark TROUBLESHOOTING.md for reference

2. **Customize Configuration**
   - Adjust sensitivity to your needs
   - Set up zone detection for specific areas
   - Configure capture settings

3. **Create Distribution** (if needed)
   - Run `./create_installer.sh`
   - Install on other Macs

4. **Optimize Performance**
   - Tune motion detection threshold
   - Adjust capture quality
   - Set up auto-cleanup for old captures

## Support

If you encounter any issues:

1. Check TROUBLESHOOTING.md
2. Run `python3 test_camera.py` for diagnostics
3. Review logs: `cat logs/motion.log`
4. Consult Motion documentation: https://motion-project.github.io/

---

**Installation Date:** _________________  
**Installed By:** _________________  
**Mac Model:** _________________  
**macOS Version:** _________________  
**Camera Model:** _________________

