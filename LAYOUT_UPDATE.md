# Layout Update - Video No Longer Overlaid

## What Changed

The application layout has been redesigned to keep the video feed completely clear of UI elements.

### Before (Overlaid Layout)
```
┌─────────────────────────────────────┐
│ [Status Text Over Video]           │ ← Overlay
│ [FPS, Zone, Alerts Over Video]     │ ← Overlay
│                                     │
│         Camera Feed                 │
│      (partially covered)            │
│                                     │
│ [Controls Text Over Video]          │ ← Overlay
└─────────────────────────────────────┘
```

### After (Border Layout)
```
┌─────────────────────────────────────┐
│ MONITORING ACTIVE                   │ ← Top Border (60px)
│ FPS: 14.6  Zone: Defined  Alerts: 1 │
├─────────────────────────────────────┤
│                                     │
│         Camera Feed                 │
│      (completely visible)           │
│         with zone overlay           │
│                                     │
├─────────────────────────────────────┤
│ D: Draw Zone                        │ ← Bottom Border (150px)
│ ENTER: Close Zone                   │
│ C: Clear Zone                       │
│ S: Start Monitoring                 │
│ P: Pause                            │
│ Q: Quit                             │
└─────────────────────────────────────┘
```

## Technical Changes

1. **Canvas Expansion**: The display canvas is now 210 pixels taller (60px top + 150px bottom)
2. **Video Placement**: Original camera feed is placed in the middle section without any text overlay
3. **Mouse Coordinates**: Click coordinates are automatically adjusted for the 60px top offset
4. **Zone Drawing**: Works correctly with offset - clicks on the video map to correct frame coordinates

## Benefits

✅ **Fully Visible Video**: No text obscuring your camera view  
✅ **Clear Zone Drawing**: See exactly where your detection zone is  
✅ **Better UX**: Status and controls in dedicated areas  
✅ **Professional Look**: Clean separation of video and UI elements

## How to Test

1. Launch the app: **Double-click** `Launch AI Motion Detection.command`
2. Press **D** to enter drawing mode
3. Click on the video to draw a zone polygon
4. Press **ENTER** to close the zone
5. Press **S** to start monitoring

The video feed should now be completely clear with all UI elements in the black borders!


