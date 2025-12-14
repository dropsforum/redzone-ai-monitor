# User Guide

Complete guide to using DROPS Red Zone Monitoring.

## Quick Start

### 1. Run the Application

```bash
cd /path/to/redzone-ai-monitor
source venv/bin/activate
python3 run_ai_app.py
```

**First run:** YOLO will automatically download a 6MB model file (~10 seconds).

### 2. Draw Your Zone

1. Press **`D`** to enter drawing mode
2. **Click** on the video feed to add points (corners of your zone)
3. Press **`ENTER`** when done (minimum 3 points)
4. The zone will appear as a green overlay

### 3. Start Monitoring

Press **`S`** to start monitoring. When a person enters your zone:
- Red bounding box appears around them
- Zone turns red
- Audible alert plays (Glass sound)
- Alert logged on screen with timestamp

## Keyboard Controls

| Key | Action |
|-----|--------|
| `D` | Enter zone drawing mode |
| `Click` | Add zone point (in drawing mode) |
| `ENTER` | Close/finish drawing zone |
| `C` | Clear current zone |
| `S` | Start monitoring |
| `P` | Pause/Resume monitoring |
| `Q` or `ESC` | Quit application |
| `M` | Cycle through cameras (camera mode only) |

## Features

✅ **AI-Powered Detection** - Uses YOLOv8 to accurately detect people (not just pixel changes)  
✅ **Custom Zone Drawing** - Draw any polygon shape to monitor specific areas  
✅ **Visual Interface** - Live camera feed with on-screen controls  
✅ **Audible Alerts** - System sound plays when person enters your zone  
✅ **Alert Cooldown** - Prevents alert spam (configurable, default 5 seconds)  
✅ **Zone Persistence** - Saves your zones between sessions  
✅ **Performance Optimized** - Runs smoothly on Apple Silicon (80-120 FPS)  
✅ **Recorded Footage Support** - Replay saved videos with full detection features

## How It Works

```
Camera → AI Detection → Zone Check → Alert
  ↓
Camera captures video
  ↓
YOLOv8 AI identifies people in frame
  ↓
Checks if person's bounding box intersects your zone
  ↓
Plays alert sound if person detected in zone
```

## Drawing Effective Zones

### Tips

- **Tip 1**: Draw zones that cover areas where you expect people to enter
- **Tip 2**: Avoid zones that include areas with frequent movement (trees, shadows)
- **Tip 3**: You can draw any shape - triangle, rectangle, pentagon, or complex polygons
- **Tip 4**: Keep zones simple (3-5 points work best)

### Example Use Cases

**Driveway Monitoring:**
```
Draw a rectangle across your driveway entrance
Only alerts when someone walks into the driveway
```

**Room Entry:**
```
Draw a zone around a doorway
Alerts when someone enters through that door
```

**Package Delivery:**
```
Draw zone at your front porch
Alerts when delivery person approaches
```

## Configuration

Edit `zones/zone_config.json` to customize settings:

```json
{
  "settings": {
    "camera_index": 0,
    "camera_width": 1280,
    "camera_height": 720,
    "camera_fps": 15,
    "video_source": "camera",
    "video_file_path": "",
    "model_size": "yolov8n.pt",
    "confidence_threshold": 0.5,
    "alert_cooldown": 5,
    "zone_overlay_alpha": 0.3
  },
  "zone_points": []
}
```

### Camera Settings

- `camera_index`: Camera device number (0, 1, 2, etc.)
- `camera_width` / `camera_height`: Resolution (default: 1280x720)
- `camera_fps`: Target frames per second (default: 15)

### Detection Settings

- `model_size`: YOLO model (`yolov8n.pt`, `yolov8s.pt`, `yolov8m.pt`)
- `confidence_threshold`: Minimum confidence (0.0-1.0, default: 0.5)
- `alert_cooldown`: Seconds between alerts (default: 5)

### Available YOLO Models

| Model | Size | Speed | Accuracy | Recommended For |
|-------|------|-------|----------|------------------|
| yolov8n.pt | 6MB | Fastest | Good | Most users (default) |
| yolov8s.pt | 22MB | Fast | Better | Higher accuracy needs |
| yolov8m.pt | 52MB | Medium | Best | Maximum accuracy |

**Recommended**: `yolov8n.pt` - perfect balance for Apple Silicon

## Using Video Files

Run the monitoring flow against prerecorded footage:

1. Open `zones/zone_config.json`
2. Set `video_source` to `"video"`
3. Provide an absolute file path in `video_file_path`

Example:

```json
{
  "settings": {
    "video_source": "video",
    "video_file_path": "/path/to/your/video/sample.mp4"
  }
}
```

**Notes:**
- Supported formats: MP4, MOV, AVI, MKV (anything OpenCV/FFmpeg can decode)
- Video loops automatically when it reaches the end
- Camera switching (`M`) is disabled while using video source
- Set `video_source` back to `"camera"` to return to live feed

## Visual Feedback

| Color | Meaning |
|-------|---------|
| 🟢 Green zone | Normal / No detection |
| 🔴 Red zone | Person in zone! |
| 🔵 Blue box | Person detected (outside zone) |
| 🔴 Red box | Person detected (in zone) |

## Performance Tips

### For Best Performance

- Keep Mac plugged in (not on battery)
- Close other resource-intensive applications
- Use `yolov8n.pt` model (default)
- Lower resolution if needed (640x480)

### For Best Accuracy

- Use `yolov8s.pt` or `yolov8m.pt` model
- Higher resolution (1280x720 or 1920x1080)
- Ensure good lighting conditions

## Advanced Usage

### Run on Startup

Create a launch script:

```bash
#!/bin/bash
cd /path/to/redzone-ai-monitor
source venv/bin/activate
python3 run_ai_app.py
```

Save as `start_monitoring.command`, make executable (`chmod +x start_monitoring.command`), double-click to run.

### Multiple Zones

Currently supports one zone. Multiple zone support can be added by:
1. Storing multiple zone lists in config
2. Checking each zone during detection
3. Labeling alerts by zone name

## Troubleshooting

### Camera Not Found

Check which camera is device 0:

```bash
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera 0:', cap.read()[0])"
```

If your camera is not device 0, edit `zones/zone_config.json`:

```json
{
  "settings": {
    "camera_index": 1
  }
}
```

### Low FPS

If FPS drops below 15:

1. Use smaller YOLO model (`yolov8n.pt`)
2. Close other applications
3. Ensure Mac is plugged in (not on battery)
4. Lower resolution if needed

### No Alert Sound

Test system sound:

```bash
afplay /System/Library/Sounds/Glass.aiff
```

If this doesn't work, check System Settings → Sound → Output

### AI Model Download

On first run, YOLOv8 will download ~6MB model file automatically. This only happens once. If download fails, check your internet connection.

For more troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review `zones/zone_config.json` for misconfigurations
3. Run with verbose output: `python3 run_ai_app.py 2>&1 | tee app.log`
4. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues


