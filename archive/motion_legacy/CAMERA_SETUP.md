# Camera Setup for Motion on macOS

## Important: How Motion Works on macOS

**Motion on macOS cannot directly access USB cameras** because:
- Motion uses V4L2 (Video4Linux) for camera access
- V4L2 only works on Linux, not macOS
- Motion on macOS can ONLY access **network cameras** (RTSP, RTMP, HTTP streams)

## The Solution

We use a two-step process:
1. **FFmpeg** captures video from your Logitech C920 camera (using macOS's AVFoundation)
2. **Media MTX** acts as an RTSP server to stream the video locally
3. **Motion** connects to this local RTSP stream

Think of it like this:
```
Logitech Camera → FFmpeg (AVFoundation) → RTSP Server → Motion
```

## Step-by-Step Setup

### 1. Install MediaMTX (RTSP Server)

```bash
brew install mediamtx
```

### 2. Start the Camera Stream

Open a **new Terminal window** and run:

```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
./scripts/start_camera_stream.sh
```

This will:
- Start the RTSP server
- Stream your Logitech C920 camera at `rtsp://localhost:8554/camera`
- Keep running (don't close this Terminal window!)

### 3. Start Motion

In a **second Terminal window**, run:

```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
source venv/bin/activate
python3 motion_app.py
```

### 4. Access the Web Interface

Open your browser to:
- **Web Control**: [http://localhost:8082](http://localhost:8082)
- **Live Stream**: [http://localhost:8083](http://localhost:8083)

## Troubleshooting

### Camera Not Found

If Motion says "No Camera device specified":
1. Make sure the camera stream script is running first
2. Check that MediaMTX is installed: `brew install mediamtx`
3. Verify FFmpeg can see your camera: `/opt/homebrew/bin/ffmpeg -f avfoundation -list_devices true -i ""`

### Port Already in Use

If port 8082 or 8083 is already in use:
1. Check what's using the port: `lsof -i :8082`
2. Kill the process or change the port in `config/motion.conf`

### Camera Permission Denied

macOS may ask for camera permissions. Go to:
**System Settings → Privacy & Security → Camera**

Allow Terminal and/or your apps to access the camera.

## Testing the Camera Stream

You can test if the RTSP stream is working before starting Motion:

```bash
# Using FFplay
/opt/homebrew/bin/ffplay rtsp://localhost:8554/camera

# Or using VLC
# File → Open Network → rtsp://localhost:8554/camera
```

## Alternative: Simpler Python + OpenCV Solution

If this setup is too complex, I can build you a simpler Python-based solution using OpenCV that:
- ✅ Works directly with macOS cameras (no RTSP needed)
- ✅ Has the same menu bar interface
- ✅ Supports zone detection
- ✅ Sends notifications

The OpenCV approach is more native to macOS and easier to maintain.

Let me know if you'd like me to switch to that approach instead!


