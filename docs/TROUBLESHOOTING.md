# Troubleshooting Guide

Common issues and solutions for DROPS Red Zone Monitoring (macOS and Windows).

## Installation Issues

### macOS: Homebrew Not Installing

**Error:** "Need sudo access on macOS"

**Solution:**
1. Ensure you have administrator privileges
2. Run the Homebrew install command in a regular Terminal (not from within this app)
3. Enter your password when prompted

### Windows: Python Not Found

**Error:** `'python' is not recognized as an internal or external command`

**Solution:**
1. Reinstall Python from [python.org](https://www.python.org/downloads/)
2. **Critical:** During installation, check "Add Python to PATH"
3. Restart your command prompt/PowerShell after installation
4. Verify: `python --version`

### Windows: PowerShell Execution Policy

**Error:** "cannot be loaded because running scripts is disabled on this system"

**Solution:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try running the setup script again.

### Dependencies Won't Install

**Error:** "Package not found" or "Failed to install"

**Solution:**
```bash
# Update Homebrew
brew update
brew upgrade

# Try installing packages individually
brew install ffmpeg
brew install pkg-config
brew install libjpeg
brew install libmicrohttpd
brew install automake
```

### Motion Build Fails

**Error:** "configure: error: libavformat not found"

**Solution:**
```bash
# Ensure FFmpeg is properly installed
brew reinstall ffmpeg

# Set PKG_CONFIG_PATH
export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"

# Try building again
./build_motion.sh
```

**Error:** "autoreconf: command not found"

**Solution:**
```bash
brew install autoconf automake libtool
```

## Camera Issues

### macOS: Camera Not Detected

**Problem:** `system_profiler SPCameraDataType` shows no cameras

**Solutions:**

1. **Check Physical Connection**
   - Unplug and reconnect USB camera
   - Try a different USB port
   - Ensure camera LED is on (if applicable)

2. **Check Other Apps**
   - Close apps that might be using camera (Zoom, FaceTime, etc.)
   - Restart your Mac
   - Test camera in Photo Booth or FaceTime

3. **Reset SMC (Intel Macs)**
   - Shut down Mac
   - Press Shift+Control+Option on left side, then power button
   - Hold for 10 seconds, release
   - Power on normally

4. **Check USB Hub**
   - If using a USB hub, try connecting directly to Mac
   - Some hubs don't provide enough power

### Windows: Camera Not Detected

**Problem:** Camera not found or not working

**Solutions:**

1. **Check Physical Connection**
   - Unplug and reconnect USB camera
   - Try a different USB port (prefer USB 3.0 ports)
   - Ensure camera LED is on (if applicable)

2. **Check Device Manager**
   - Open Device Manager (Win+X > Device Manager)
   - Look under "Cameras" or "Imaging devices"
   - If camera shows with yellow warning, update drivers

3. **Check Other Apps**
   - Close apps using camera (Zoom, Teams, Skype, etc.)
   - Check Task Manager for camera processes
   - Restart Windows if needed

4. **Update Camera Drivers**
   - Right-click camera in Device Manager > Update driver
   - Or download drivers from manufacturer website

5. **Test Camera**
   - Use Windows Camera app to verify camera works
   - Check if camera works in other applications

### macOS: Camera Permission Denied

**Problem:** Motion can't access camera

**Solutions:**

1. **Grant Permission in System Settings**
   - Open System Settings > Privacy & Security > Camera
   - Enable camera for Terminal (during development)
   - Enable camera for Motion Detector app (when bundled)

2. **Reset Permissions**
   ```bash
   # Reset camera permissions (requires restart)
   sudo tccutil reset Camera
   ```
   Then restart your Mac and grant permissions again

3. **Run with Permissions**
   ```bash
   # When testing, run from Terminal that has camera access
   cd /path/to/redzone-ai-monitor
   source venv/bin/activate
   python3 motion_app.py
   ```

### Windows: Camera Permission Denied

**Problem:** Application can't access camera

**Solutions:**

1. **Grant Permission in Windows Settings**
   - Open Settings > Privacy & Security > Camera
   - Enable "Let apps access your camera"
   - Enable camera for Python or the application

2. **Check Antivirus/Firewall**
   - Some antivirus software blocks camera access
   - Temporarily disable to test, then add exception

3. **Run as Administrator**
   - Right-click Command Prompt/PowerShell
   - Select "Run as administrator"
   - Try running the application again

### Wrong Camera Selected

**Problem:** Application using wrong camera (if you have multiple)

**Solution:**

Edit `zones/zone_config.json` and specify the camera index:

```json
{
  "settings": {
    "camera_index": 1  // Try 0, 1, 2, etc. until you find the right camera
  }
}
```

**To find available cameras:**

**macOS/Linux:**
```bash
python3 -c "import cv2; [print(f'Camera {i}: {cv2.VideoCapture(i).read()[0]}') for i in range(10)]"
```

**Windows:**
```cmd
python -c "import cv2; [print(f'Camera {i}: {cv2.VideoCapture(i).read()[0]}') for i in range(10)]"
```

## Motion Detection Issues

### No Motion Detected

**Problem:** Waving in front of camera produces no alerts

**Solutions:**

1. **Lower Threshold**
   
   Edit `config/motion.conf`:
   ```conf
   threshold 1500  # Lower = more sensitive
   ```

2. **Check Event Gap**
   
   Edit `config/motion.conf`:
   ```conf
   event_gap 5  # Reduce to allow more frequent events
   ```

3. **Verify Motion is Running**
   ```bash
   ps aux | grep motion
   # Should show motion process
   ```

4. **Check Logs**
   ```bash
   tail -f logs/motion.log
   # Watch for motion detection messages
   ```

5. **Test Without Zone Mask**
   
   Edit `config/motion.conf` and comment out:
   ```conf
   # mask_file /path/to/mask.png
   ```

### Too Many False Positives

**Problem:** Constant motion alerts from shadows, lighting changes

**Solutions:**

1. **Increase Threshold**
   
   Edit `config/motion.conf`:
   ```conf
   threshold 4000  # Higher = less sensitive
   ```

2. **Enable Lightswitch Filter**
   
   Edit `config/motion.conf`:
   ```conf
   lightswitch_percent 10  # Ignore sudden lighting changes
   ```

3. **Adjust Noise Level**
   
   Edit `config/motion.conf`:
   ```conf
   noise_level 64
   noise_tune on
   ```

4. **Use Smart Mask**
   
   Edit `config/motion.conf`:
   ```conf
   smart_mask_speed 5  # Learns and ignores static areas
   ```

5. **Increase Minimum Frames**
   
   Edit `config/motion.conf`:
   ```conf
   minimum_motion_frames 5  # Requires motion in multiple frames
   ```

6. **Use Zone Masking**
   - Create a mask image (white = detect, black = ignore)
   - Mask out areas with trees, curtains, etc.
   - Save as `config/zones/mask.png`

### Motion Detected in Wrong Area

**Problem:** Getting alerts from areas you want to ignore

**Solution:** Create a zone mask

1. Start monitoring and view feed: http://localhost:8081
2. Take screenshot of camera view
3. Open in image editor (Preview, GIMP, etc.)
4. Paint areas to monitor in WHITE
5. Paint areas to ignore in BLACK
6. Save as PNG: `config/zones/mask.png`
7. Edit `config/motion.conf`:
   ```conf
   mask_file /absolute/path/to/config/zones/mask.png
   ```
8. Restart monitoring

## Application Issues

### Menu Bar Icon Not Appearing

**Problem:** App runs but no icon in menu bar

**Solutions:**

1. **Check if rumps is installed**
   ```bash
   source venv/bin/activate
   python3 -c "import rumps; print('OK')"
   ```

2. **Grant Accessibility Permissions**
   - System Settings > Privacy & Security > Accessibility
   - Add Terminal or Python

3. **Try Running Directly**
   ```bash
   python3 -c "import rumps; rumps.App('Test').run()"
   ```

### No Notifications Appearing

**Problem:** Motion detected but no macOS notifications

**Solutions:**

1. **Enable Notifications**
   - System Settings > Notifications
   - Find Terminal or Python
   - Enable notifications, banners, and sounds

2. **Test Notifications**
   ```bash
   python3 notification_handler.py
   ```

3. **Check Notification Cooldown**
   
   Edit `notification_handler.py`:
   ```python
   self.notification_cooldown = 2  # Reduce from 5 seconds
   ```

4. **Manual Notification Test**
   ```bash
   osascript -e 'display notification "Test" with title "Test"'
   ```

### Motion Won't Start

**Problem:** "Motion failed to start" error

**Solutions:**

1. **Check if Already Running**
   ```bash
   ps aux | grep motion
   # Kill if found
   killall motion
   ```

2. **Check Port Availability**
   ```bash
   lsof -i :8080
   lsof -i :8081
   ```
   
   If ports are in use, edit `config/motion.conf`:
   ```conf
   webcontrol_port 8082
   stream_port 8083
   ```

3. **Verify Config File**
   ```bash
   python3 test_camera.py
   ```

4. **Check Motion Binary**
   ```bash
   ls -la motion_install/bin/motion
   ./motion_install/bin/motion --version
   ```

5. **Review Logs**
   ```bash
   cat logs/motion.log
   ```

6. **Test Motion Manually**
   ```bash
   ./motion_install/bin/motion -c config/motion.conf -n
   # -n runs in non-daemon mode for debugging
   ```

### Motion Won't Stop

**Problem:** Motion process continues after clicking "Stop"

**Solution:**

```bash
# Find process ID
ps aux | grep motion

# Force kill
killall -9 motion

# Or by PID
kill -9 <PID>

# Clean up PID file
rm logs/motion.pid
```

## Web Interface Issues

### Can't Access Web Interface

**Problem:** http://localhost:8080 not loading

**Solutions:**

1. **Check Motion is Running**
   ```bash
   ps aux | grep motion
   ```

2. **Verify Port Configuration**
   
   Check `config/motion.conf`:
   ```conf
   webcontrol_port 8080
   webcontrol_localhost off
   ```

3. **Try Different Browser**
   - Safari, Chrome, Firefox

4. **Check Firewall**
   - System Settings > Network > Firewall
   - Allow Motion or disable temporarily

5. **Test Direct Connection**
   ```bash
   curl http://localhost:8080
   ```

### Can't See Camera Stream

**Problem:** Web interface loads but no video stream

**Solutions:**

1. **Check Stream Port**
   
   Edit `config/motion.conf`:
   ```conf
   stream_port 8081
   stream_localhost off
   ```

2. **Access Stream Directly**
   - Go to: http://localhost:8081

3. **Check Stream Quality**
   
   Edit `config/motion.conf`:
   ```conf
   stream_quality 50  # Lower quality uses less bandwidth
   stream_maxrate 10  # Lower framerate
   ```

## Performance Issues

### High CPU Usage

**Problem:** Motion using too much CPU

**Solutions:**

1. **Reduce Frame Rate**
   
   Edit `config/motion.conf`:
   ```conf
   framerate 10  # Lower from 15
   ```

2. **Reduce Resolution**
   
   Edit `config/motion.conf`:
   ```conf
   width 320
   height 240
   ```

3. **Disable Features**
   
   Edit `config/motion.conf`:
   ```conf
   movie_output off  # Disable video recording
   snapshot_interval 0  # Disable snapshots
   ```

4. **Optimize Detection**
   
   Edit `config/motion.conf`:
   ```conf
   despeckle_filter EedDl  # Reduce processing
   smart_mask_speed 0  # Disable smart mask
   ```

### Disk Space Issues

**Problem:** Captures folder filling up disk

**Solutions:**

1. **Auto-Delete Old Captures**
   
   Create cleanup script:
   ```bash
   # Delete captures older than 7 days
   find captures/ -type f -mtime +7 -delete
   ```

2. **Reduce Capture Size**
   
   Edit `config/motion.conf`:
   ```conf
   picture_quality 50  # Lower quality
   movie_quality 50
   ```

3. **Limit Movie Length**
   
   Edit `config/motion.conf`:
   ```conf
   max_movie_time 30  # Seconds
   ```

4. **Manual Cleanup**
   ```bash
   # Delete all captures
   rm -rf captures/*
   
   # Or just old ones
   find captures/ -type f -mtime +1 -delete
   ```

## Getting More Help

### Check Logs

```bash
# Motion log
tail -f logs/motion.log

# Event log
tail -f logs/events.log

# System log (for macOS issues)
log show --predicate 'process == "motion"' --last 5m
```

### Run Diagnostics

```bash
python3 test_camera.py
```

### Enable Debug Mode

Edit `config/motion.conf`:
```conf
log_level 9  # Maximum verbosity
log_type all
```

### Motion Documentation

For advanced configuration options, see:
- [Motion Project Documentation](https://motion-project.github.io/)
- [Motion Configuration Reference](https://motion-project.github.io/motion_config.html)

### Report Issues

If you find bugs or need help:

**macOS:**
1. Check logs: `logs/motion.log`
2. Run diagnostics: `python3 scripts/test_ai_performance.py`
3. Document the error messages
4. Note your macOS version and camera model

**Windows:**
1. Check application output in console
2. Run diagnostics: `python scripts\test_ai_performance.py`
3. Document the error messages
4. Note your Windows version and camera model
5. Include Python version: `python --version`


