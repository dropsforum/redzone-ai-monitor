# Quick Start - AI Motion Detection

## Step 1: Run the App

```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
source venv/bin/activate
python3 run_ai_app.py
```

**First run**: YOLO will download a 6MB model file (one time only, ~10 seconds)

## Step 2: Draw Your Zone

1. Press **`D`** (Draw mode)
2. **Click** on the video to add points
3. Press **`ENTER`** to close the zone

**Tip**: Draw a polygon around the area you want to monitor (e.g., doorway, driveway)

## Step 3: Start Monitoring

Press **`S`** to start monitoring

## Step 4: Test It!

Walk into the zone you drew - you should hear an alert sound!

---

## All Keyboard Controls

- **`D`** - Draw zone
- **`ENTER`** - Finish zone
- **`C`** - Clear zone
- **`S`** - Start monitoring
- **`P`** - Pause
- **`Q`** - Quit

---

## Troubleshooting

### "No camera found"

Check which camera is device 0:
```bash
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera 0:', cap.read()[0])"
```

### "Low FPS"

Make sure your MacBook is plugged in (not on battery)

### "No alert sound"

Test your system sound:
```bash
afplay /System/Library/Sounds/Glass.aiff
```

---

## What Happens When Person Detected?

✅ Red bounding box around person  
✅ Zone turns red  
✅ Alert sound plays (Glass.aiff)  
✅ Alert logged on screen with timestamp  

---

That's it! The app saves your zone automatically, so next time you run it, your zone will be loaded.



