# Quick Test - Verify Everything Works

## Step 1: Test FFmpeg Can See Your Camera

```bash
/opt/homebrew/bin/ffmpeg -f avfoundation -list_devices true -i ""
```

You should see:
- `[0] HD Pro Webcam C920` ✓
- `[1] Studio Display Camera` ✓

## Step 2: Test Capturing from Camera

```bash
/opt/homebrew/bin/ffmpeg -f avfoundation -framerate 15 -i "0" -t 5 -y /tmp/test.mp4
```

This captures 5 seconds of video. If it works without errors, your camera is accessible!

## Step 3: Install MediaMTX

```bash
brew install mediamtx
```

## Step 4: Test the Full Pipeline

**Terminal 1 - Start Camera Stream:**
```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
./scripts/start_camera_stream.sh
```

Wait for it to say "Streaming Logitech C920 to RTSP..."

**Terminal 2 - Test Motion:**
```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
~/.motion_install/bin/motion -n -c config/motion.conf
```

Watch the output. You should see:
- ✓ "Camera found"
- ✓ "Webcontrol started on port 8082"  
- ✓ No errors about "No Camera device specified"

## Step 5: View the Stream

Open: [http://localhost:8082](http://localhost:8082)

You should see your camera feed!

## If It Works

Great! You can now use the menu bar app:

```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
source venv/bin/activate
python3 motion_app.py
```

## If It Doesn't Work

Please send me:
1. The complete output from Terminal 1 (camera stream)
2. The complete output from Terminal 2 (Motion)
3. The last 50 lines of `/Volumes/Data Vault/Cursor 2/Motion/logs/motion.log`

And I'll help troubleshoot!


