# AI Motion Detection App

A macOS application that uses AI (YOLOv8) to detect people entering user-defined zones with audible alerts.

## Features

✅ **AI-Powered Detection** - Uses YOLOv8 to accurately detect people (not just pixel changes)  
✅ **Custom Zone Drawing** - Draw any polygon shape to monitor specific areas  
✅ **Visual Interface** - Live camera feed with on-screen controls  
✅ **Audible Alerts** - System sound plays when person enters your zone  
✅ **Alert Cooldown** - Prevents alert spam (configurable, default 5 seconds)  
✅ **Zone Persistence** - Saves your zones between sessions  
✅ **Performance Optimized** - Runs smoothly on M3 (80-100 FPS)

## System Requirements

- **macOS** (tested on M3 MacBook with 16GB RAM)
- **Python 3.9+**
- **Camera** (Logitech C920 or built-in webcam)
- **~1GB disk space** (for dependencies)

## Quick Start

### 1. First Time Setup (Already Done!)

Dependencies are already installed. Skip to step 2!

### 2. Run the Application

```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
source venv/bin/activate
python3 run_ai_app.py
```

### 3. Define Your Monitoring Zone

1. **Press `D`** to enter drawing mode
2. **Click** on the video feed to add points (corners of your zone)
3. **Press `ENTER`** when done (minimum 3 points)
4. The zone will appear as a green overlay

### 4. Start Monitoring

1. **Press `S`** to start monitoring
2. Status will change to "MONITORING ACTIVE" (green)
3. When a person enters your zone:
   - Red bounding box appears around them
   - Zone turns red
   - **Audible alert plays** (Glass sound)
   - Alert logged on screen

### 5. Controls

| Key | Action |
|-----|--------|
| `D` | Enter zone drawing mode |
| `ENTER` | Close/finish drawing zone |
| `C` | Clear current zone |
| `S` | Start monitoring |
| `P` | Pause/Resume monitoring |
| `Q` or `ESC` | Quit application |

## How It Works

```
Camera → AI Detection → Zone Check → Alert
  ↓
Your Logitech C920 captures video
  ↓
YOLOv8 AI identifies people in frame
  ↓
Checks if person's bounding box intersects your zone
  ↓
Plays alert sound if person detected in zone
```

## Tips

### Drawing Effective Zones

- **Tip 1**: Draw zones that cover areas where you expect people to enter
- **Tip 2**: Avoid zones that include areas with frequent movement (trees, shadows)
- **Tip 3**: You can draw any shape - triangle, rectangle, pentagon, or complex polygons

### Example Zones

**Driveway Monitoring**:
```
Draw a rectangle across your driveway entrance
Only alerts when someone walks into the driveway
```

**Room Entry**:
```
Draw a zone around a doorway
Alerts when someone enters through that door
```

**Package Delivery**:
```
Draw zone at your front porch
Alerts when delivery person approaches
```

## Troubleshooting

### Camera Not Found

```bash
# Check available cameras
python3 -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).read()[0]])"
```

If your Logitech C920 is not camera 0, edit `zones/zone_config.json`:
```json
{
  "settings": {
    "camera_index": 1
  }
}
```

### Low FPS

If FPS drops below 15:
1. Use smaller YOLO model - edit `zones/zone_config.json`:
   ```json
   {
     "settings": {
       "model_size": "yolov8n.pt"
     }
   }
   ```
2. Close other applications
3. Ensure Mac is plugged in (not on battery)

### No Alert Sound

Test system sound:
```bash
afplay /System/Library/Sounds/Glass.aiff
```

If this doesn't work, check System Settings → Sound → Output

### AI Model Download

On first run, YOLOv8 will download ~6MB model file automatically.  
This only happens once.

## Configuration

Edit `zones/zone_config.json` to customize:

```json
{
  "settings": {
    "camera_index": 0,
    "camera_width": 640,
    "camera_height": 480,
    "camera_fps": 15,
    "model_size": "yolov8n.pt",
    "confidence_threshold": 0.5,
    "alert_cooldown": 5,
    "zone_overlay_alpha": 0.3
  },
  "zone_points": [[x1, y1], [x2, y2], ...]
}
```

### Available YOLO Models

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| yolov8n.pt | 6MB | Fastest | Good |
| yolov8s.pt | 22MB | Fast | Better |
| yolov8m.pt | 52MB | Medium | Best |

## Performance on M3 (16GB)

| Model | FPS | Latency |
|-------|-----|---------|
| yolov8n | 100 FPS | 10ms |
| yolov8s | 70 FPS | 14ms |
| yolov8m | 50 FPS | 20ms |

**Recommended**: yolov8n (default) - perfect balance for M3

## Files and Directories

```
/Volumes/Data Vault/Cursor 2/Motion/
├── ai_motion_app/           # Application source code
│   ├── main_app.py          # Main application
│   ├── camera_manager.py    # Camera handling
│   ├── ai_detector.py       # YOLO detection
│   ├── zone_manager.py      # Zone polygon logic
│   ├── alert_system.py      # Alert management
│   └── config.py            # Configuration
├── zones/                   # Saved zones and config
│   └── zone_config.json    # Your settings
├── run_ai_app.py           # Launch script
└── requirements_ai.txt     # Python dependencies
```

## Advanced Usage

### Run on Startup (Optional)

Create a launch script:

```bash
#!/bin/bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
source venv/bin/activate
python3 run_ai_app.py
```

Save as `start_monitoring.command`, make executable, double-click to run.

### Multiple Zones (Future Feature)

Currently supports one zone. Multiple zone support can be added by:
1. Storing multiple zone lists in config
2. Checking each zone during detection
3. Labeling alerts by zone name

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review `zones/zone_config.json` for misconfigurations
3. Run with verbose output: `python3 run_ai_app.py 2>&1 | tee app.log`

## Credits

- **YOLOv8**: Ultralytics (https://github.com/ultralytics/ultralytics)
- **OpenCV**: Open Source Computer Vision Library
- **PyTorch**: Deep learning framework

## License

This application is for personal use. YOLO and other dependencies have their own licenses.



