# Motion Detection Mac App

A macOS application that uses Motion software to detect objects entering specific camera zones with manual activation and notifications.

## Features

- Manual start/stop control via menu bar
- Zone-based motion detection (detect only in specific camera areas)
- macOS notifications when motion detected
- Live camera feed viewing via web interface
- Works with Logitech and other USB cameras

## Installation (Development)

### Prerequisites

This installation requires administrator privileges on your Mac.

### Step 1: Install Homebrew (if not already installed)

Run this command in Terminal:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After installation, follow the prompts to add Homebrew to your PATH.

### Step 2: Run the Setup Script

```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
chmod +x setup_dependencies.sh
./setup_dependencies.sh
```

This will:
- Install required system dependencies (ffmpeg, libmicrohttpd, etc.)
- Clone and build Motion from source
- Install Python dependencies for the wrapper app

### Step 3: Test the Installation

```bash
python3 test_camera.py
```

This will list available cameras and test Motion configuration.

## Usage

### Start the Menu Bar App

```bash
python3 motion_app.py
```

The app icon will appear in your menu bar. Click it to:
- Start/Stop motion detection
- View camera feed
- Access settings
- View recent alerts

### Configure Detection Zone

1. Start the app and click "Start Monitoring"
2. Open the web interface (http://localhost:8080)
3. View the camera feed and note the areas you want to monitor
4. Stop monitoring and edit `config/motion.conf`
5. Set up the mask/zone for your specific detection area

## Project Structure

```
Motion/
├── README.md                   # This file
├── setup_dependencies.sh       # Install system dependencies
├── build_motion.sh            # Build Motion from source
├── motion_app.py              # Main menu bar application
├── motion_manager.py          # Motion process management
├── notification_handler.py    # macOS notifications
├── event_listener.py          # Motion event monitoring
├── requirements.txt           # Python dependencies
├── config/
│   ├── motion.conf           # Motion configuration
│   └── zones/                # Zone mask images
├── motion_build/             # Motion source code (git clone)
├── logs/                     # Application logs
└── captures/                 # Motion detection captures

```

## Distribution Package

To create an installer for other Macs:

```bash
./create_installer.sh
```

This creates a .pkg installer in the `dist/` directory.

## Troubleshooting

### Camera Permission Issues

macOS requires explicit camera permissions. If the camera doesn't work:

1. Go to System Settings > Privacy & Security > Camera
2. Enable camera access for Terminal (during development) or the Motion app

### Motion Not Detecting

- Check camera connection: `ls /dev/video*`
- Verify Motion is running: `ps aux | grep motion`
- Check Motion logs: `tail -f logs/motion.log`

### Port Already in Use

If port 8080 is in use, edit `config/motion.conf` and change the `stream_port` value.

## Technical Details

- **Motion**: Open-source motion detection software
- **Python App**: Menu bar interface using rumps library
- **Notifications**: Native macOS notifications via osascript
- **Camera Support**: V4L2-compatible cameras on macOS


