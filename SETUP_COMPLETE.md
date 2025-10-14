# ✅ Setup Complete!

**Congratulations!** Your Motion Detection Mac App is fully installed and ready to use.

## 🎥 Detected Cameras

Your Mac has 2 cameras available:
1. **HD Pro Webcam C920** (Logitech) - Your external camera
2. **Studio Display Camera** - Built-in display camera

## 🚀 How to Start the App

### Option 1: Quick Start (Recommended)
```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
./run_app.sh
```

### Option 2: Manual Start
```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
source venv/bin/activate
python3 motion_app.py
```

## 📱 Using the App

Once started, you'll see an icon in your Mac's menu bar:
- **💤** = Not monitoring (idle)
- **👁️** = Actively monitoring

### Menu Options

Click the menu bar icon to access:
- **Start Monitoring** - Begin motion detection
- **Stop Monitoring** - Stop detection
- **View Camera Feed** - Opens http://localhost:8081 in browser
- **Open Captures Folder** - View saved images/videos
- **Status** - Check current state
- **Quit** - Exit the application

## 🔔 Notifications

When motion is detected in the camera view:
- You'll receive a macOS notification
- An image will be saved to the `captures/` folder
- Optionally, a video will be recorded

## ⚙️ Configuration

Your Motion configuration is located at:
```
config/motion.conf
```

### Key Settings You Can Adjust

**Detection Sensitivity:**
```conf
threshold 2500  # Lower = more sensitive (1500-4500 recommended)
```

**Event Gap (time between detections):**
```conf
event_gap 10  # Seconds between motion events
```

**Capture Settings:**
```conf
picture_output on   # Save images
movie_output on     # Save videos
movie_quality 75    # Video quality (1-100)
```

**Web Interface:**
```conf
webcontrol_port 8080  # Change if port is in use
stream_port 8081      # Change if port is in use
```

## 🎯 Setting Up Zone Detection

To detect motion only in specific areas (like a doorway):

### Step 1: View Your Camera
1. Start monitoring: Click menu icon > "Start Monitoring"
2. Open stream: Click menu icon > "View Camera Feed"
3. Your browser will open showing the live camera view

### Step 2: Create a Zone Mask

Run the zone mask helper:
```bash
python3 create_zone_mask.py
```

Or manually:
1. Take a screenshot of the camera view
2. Open in an image editor (Preview, Photoshop, GIMP)
3. Create a new layer with same dimensions (640x480 by default)
4. Paint WHITE on areas where you WANT to detect motion
5. Paint BLACK on areas you want to IGNORE
6. Export as PNG: `config/zones/mask.png`

### Step 3: Enable the Mask

Edit `config/motion.conf` and uncomment this line:
```conf
mask_file /Volumes/Data Vault/Cursor 2/Motion/config/zones/mask.png
```

Then restart monitoring (Stop > Start).

## 📂 Directory Structure

```
Motion/
├── motion_app.py           # Main application
├── run_app.sh              # Quick launcher
├── config/
│   └── motion.conf         # Configuration file
├── captures/               # Saved images/videos
├── logs/                   # Log files
│   ├── motion.log          # Motion engine log
│   └── events.log          # Event log
└── scripts/                # Event handler scripts
```

## 🔧 Troubleshooting

### Camera Not Working

1. **Check Permissions:**
   - System Settings > Privacy & Security > Camera
   - Enable for Terminal or Python

2. **Check if Camera is In Use:**
   - Close other apps using camera (Zoom, FaceTime, etc.)

3. **Test Camera:**
   ```bash
   python3 test_camera.py
   ```

### Motion Not Detecting

1. **Lower Threshold:**
   Edit `config/motion.conf`:
   ```conf
   threshold 1500  # More sensitive
   ```

2. **Check Event Gap:**
   ```conf
   event_gap 5  # Allow more frequent events
   ```

3. **View Logs:**
   ```bash
   tail -f logs/motion.log
   ```

### No Notifications

1. **Enable Notifications:**
   - System Settings > Notifications
   - Find Terminal or Python
   - Enable notifications

2. **Test Notifications:**
   ```bash
   python3 notification_handler.py
   ```

### Port Already in Use

If you get port errors, edit `config/motion.conf`:
```conf
webcontrol_port 8082
stream_port 8083
```

## 📊 Viewing Captures

### Via Menu Bar
Click menu icon > "Open Captures Folder"

### Via Terminal
```bash
open captures/
```

### Via Finder
Navigate to:
```
/Volumes/Data Vault/Cursor 2/Motion/captures/
```

## 🎬 Advanced Usage

### Adjust Video Quality

Edit `config/motion.conf`:
```conf
picture_quality 90  # Higher = better quality (1-100)
movie_quality 85    # Higher = better quality (1-100)
```

### Disable Video Recording

Edit `config/motion.conf`:
```conf
movie_output off  # Only save images
```

### Change Frame Rate

Edit `config/motion.conf`:
```conf
framerate 10  # Lower = less CPU usage
```

### Add Authentication

Edit `config/motion.conf`:
```conf
webcontrol_authentication username:password
stream_authentication username:password
```

## 📦 Creating Installer for Other Macs

To create a distributable package:

```bash
./create_installer.sh
```

This creates:
- `dist/MotionDetector-v1.0.0.dmg` - Disk image installer
- `dist/MotionDetector-v1.0.0.pkg` - Package installer

Copy either file to another Mac and install.

## 📝 Daily Usage

### Starting Monitoring

1. Open the app: `./run_app.sh`
2. Click the menu bar icon (💤)
3. Select "Start Monitoring"
4. Icon changes to 👁️
5. You'll receive notification: "Monitoring Started"

### When Motion is Detected

- macOS notification appears
- Image saved to `captures/` folder
- Event logged to `logs/events.log`

### Stopping Monitoring

1. Click menu bar icon (👁️)
2. Select "Stop Monitoring"
3. Icon changes to 💤
4. You'll receive notification: "Monitoring Stopped"

## 🔗 Useful Links

- **Live Camera Feed:** [http://localhost:8081](http://localhost:8081)
- **Web Control Interface:** [http://localhost:8080](http://localhost:8080)
- **Motion Documentation:** [https://motion-project.github.io/](https://motion-project.github.io/)

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Start App | `./run_app.sh` |
| Test System | `python3 test_camera.py` |
| View Captures | `open captures/` |
| View Logs | `tail -f logs/motion.log` |
| Edit Config | `open config/motion.conf` |
| Create Zone Mask | `python3 create_zone_mask.py` |

## ✨ Tips & Best Practices

1. **Test First**: Start monitoring and wave in front of camera to test
2. **Adjust Sensitivity**: Fine-tune `threshold` based on your needs
3. **Use Zone Masks**: Ignore areas with trees, curtains, or busy streets
4. **Check Captures**: Periodically review and delete old captures
5. **Monitor Disk Space**: Videos can use significant storage
6. **Lighting**: Motion detection works best with consistent lighting

## 🎯 Next Steps

1. **Start the app** and test motion detection
2. **View the camera feed** to see what Motion sees
3. **Create a zone mask** for specific-area detection
4. **Adjust sensitivity** based on your environment
5. **Set up notifications** preferences

---

**You're all set!** Enjoy your motion detection system! 🎉

For detailed troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)



