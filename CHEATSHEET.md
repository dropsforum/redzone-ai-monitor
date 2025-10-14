# AI Motion Detection - Cheat Sheet

## 🏃 Quick Start

```bash
cd "/Volumes/Data Vault/Cursor 2/Motion"
source venv/bin/activate
python3 run_ai_app.py
```

---

## ⌨️ Keyboard Controls

| Key | Action |
|:---:|--------|
| **D** | Enter drawing mode |
| **Click** | Add zone point |
| **ENTER** | Close zone |
| **C** | Clear zone |
| **S** | Start monitoring |
| **P** | Pause/Resume |
| **Q** | Quit |

---

## 📍 Workflow

1. **Press D** → Click points → **Press ENTER**
2. **Press S** → Monitoring active
3. Walk into zone → Alert plays

---

## 🎨 Visual Feedback

| Color | Meaning |
|-------|---------|
| 🟢 Green zone | Normal / No detection |
| 🔴 Red zone | Person in zone! |
| 🔵 Blue box | Person detected (outside zone) |
| 🔴 Red box | Person detected (in zone) |

---

## 📁 Files

- **Config**: `zones/zone_config.json`
- **Docs**: `AI_APP_README.md`
- **This Mac**: M3, 16GB RAM, ~100 FPS

---

## 🔧 Quick Fixes

**No camera?**
```bash
python3 -c "import cv2; print(cv2.VideoCapture(0).read()[0])"
```

**Test sound?**
```bash
afplay /System/Library/Sounds/Glass.aiff
```

**Low FPS?**
- Plug in MacBook
- Close other apps

---

## 💡 Tips

- Draw **simple zones** (3-5 points)
- **Avoid** areas with trees/shadows
- Zone saves automatically
- Alert cooldown = 5 seconds

---

**That's it! Have fun monitoring! 🎉**



