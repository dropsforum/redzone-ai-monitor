# Quick Start Guide

Get up and running with the Motion Detection Mac App in just a few steps!

## Prerequisites

- macOS (tested on macOS 10.15+)
- Administrator access
- Logitech USB camera (or any compatible webcam)
- Internet connection (for initial setup)

## Step 1: Install Homebrew

If you don't have Homebrew installed, open Terminal and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the prompts and add Homebrew to your PATH as instructed.

## Step 2: Install Dependencies

Navigate to the project directory and run the setup script:

```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
chmod +x setup_dependencies.sh
./setup_dependencies.sh
```

This will install:
- FFmpeg and other system libraries
- Python dependencies
- Create necessary directories

## Step 3: Build Motion

Build Motion from source:

```bash
chmod +x build_motion.sh
./build_motion.sh
```

This will:
- Clone the Motion repository
- Compile Motion for your Mac
- Install it locally in the project directory

**Note:** This step may take 5-10 minutes depending on your Mac's speed.

## Step 4: Create Configuration

Generate the Motion configuration file:

```bash
source venv/bin/activate
python3 create_config.py
```

This creates:
- `config/motion.conf` - Main configuration
- `scripts/` - Event handler scripts
- Directory structure for captures and logs

## Step 5: Test Your Setup

Verify everything is working:

```bash
python3 test_camera.py
```

This will check:
- Camera detection
- Motion installation
- Configuration validity
- Python dependencies

## Step 6: Grant Camera Permissions

1. Open **System Settings** > **Privacy & Security** > **Camera**
2. When prompted, allow camera access for Terminal or Python
3. If you don't see a prompt, the app may need to request it later

## Step 7: Run the App

Start the menu bar application:

```bash
python3 motion_app.py
```

You should see a new icon (💤) appear in your menu bar!

## Step 8: Start Monitoring

1. Click the menu bar icon
2. Select **"Start Monitoring"**
3. The icon changes to 👁️ to indicate monitoring is active
4. Click **"View Camera Feed"** to see the live stream

## Configuring Zone Detection

To detect motion only in specific areas:

1. Start monitoring and view the camera feed (http://localhost:8081)
2. Take a screenshot of the camera view
3. Use an image editor to create a mask:
   - White areas = detect motion
   - Black areas = ignore motion
4. Save the mask as `config/zones/mask.png`
5. Edit `config/motion.conf` and uncomment the line:
   ```
   mask_file /path/to/config/zones/mask.png
   ```
6. Restart monitoring

## Testing Motion Detection

To test if motion detection is working:

1. Start monitoring
2. Wave your hand in front of the camera
3. You should receive a macOS notification
4. Check the `captures/` folder for saved images/videos

## Troubleshooting

### "Camera Not Detected"

- Check camera is plugged in
- Try unplugging and reconnecting
- Ensure no other app is using the camera
- Grant camera permissions in System Settings

### "Motion Failed to Start"

- Check logs: `cat logs/motion.log`
- Verify config: `python3 test_camera.py`
- Try rebuilding: `./build_motion.sh`

### "Port Already in Use"

Edit `config/motion.conf` and change:
```
webcontrol_port 8082
stream_port 8083
```

### "No Notifications Appearing"

- Check notification permissions for Terminal/Python
- System Settings > Notifications > Allow notifications
- Test manually: `python3 notification_handler.py`

## Customization

### Adjust Sensitivity

Edit `config/motion.conf` and change the `threshold` value:
- Lower = more sensitive (more false positives)
- Higher = less sensitive (might miss motion)
- Default: 2500
- Try range: 1500-4500

### Change Image Quality

Edit `config/motion.conf`:
```
picture_quality 90
movie_quality 85
```

### Disable Video Recording

Edit `config/motion.conf`:
```
movie_output off
```

### Change Event Gap

Edit `config/motion.conf`:
```
event_gap 20
```
This sets minimum seconds between motion events.

## Daily Usage

### Starting the App

```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
source venv/bin/activate
python3 motion_app.py
```

### Viewing Captures

Click the menu bar icon and select **"Open Captures Folder"**

Or directly:
```bash
open captures/
```

### Stopping Monitoring

Click the menu bar icon and select **"Stop Monitoring"**

### Quitting the App

Click the menu bar icon and select **"Quit"**

## Next Steps

- Configure zone-based detection for specific areas
- Adjust motion sensitivity in config
- Set up automatic startup (optional)
- Create distribution package for other Macs

For more detailed information, see [README.md](README.md)

## Getting Help

If you encounter issues:

1. Check the logs: `logs/motion.log`
2. Run diagnostics: `python3 test_camera.py`
3. Review configuration: `config/motion.conf`
4. Check Motion documentation: https://motion-project.github.io/


