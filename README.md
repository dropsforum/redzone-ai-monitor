# DROPS Red Zone Monitoring

A cross-platform application (macOS and Windows) that uses AI (YOLOv8) to detect people entering user-defined zones with audible alerts.

## Features

✅ **AI-Powered Detection** - Uses YOLOv8 to accurately detect people (not just pixel changes)  
✅ **Custom Zone Drawing** - Draw any polygon shape to monitor specific areas  
✅ **Visual Interface** - Live camera feed with on-screen controls  
✅ **Audible Alerts** - System sound plays when person enters your zone  
✅ **Alert Cooldown** - Prevents alert spam (configurable)  
✅ **Zone Persistence** - Saves your zones between sessions  
✅ **Performance Optimized** - Runs smoothly on Apple Silicon (80-120 FPS) and modern Windows PCs  
✅ **Recorded Footage Support** - Replay saved videos with full detection features

## Quick Start

### macOS

1. **Install dependencies:**
   ```bash
   ./scripts/setup_dependencies.sh
   ```

2. **Run the application:**
   ```bash
   source venv/bin/activate
   python3 run_ai_app.py
   ```

### Windows

1. **Install dependencies:**
   ```powershell
   .\scripts\setup_dependencies.ps1
   ```
   Or if PowerShell is not available:
   ```cmd
   scripts\setup_dependencies.bat
   ```

2. **Run the application:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   python run_ai_app.py
   ```

### Easiest Windows build (recommended)

If you just want a Windows `.exe` without setting up a Windows build environment, GitHub can build it for you:

1. Push your latest code to GitHub
2. Open your repo on GitHub and click the **Actions** tab
3. Click **Build Windows EXE**
4. Click **Run workflow**
5. When it finishes, download the artifact **DROPS-Red-Zone-Monitoring-Windows** and unzip it
6. Run `DROPS Red Zone Monitoring.exe`

### Using the Application

3. **Draw your zone:** Press `D`, click points, press `ENTER`

4. **Start monitoring:** Press `S`

For detailed instructions, see [docs/INSTALLATION.md](docs/INSTALLATION.md) and [docs/USAGE.md](docs/USAGE.md).

## System Requirements

### macOS
- **macOS** 10.15 or later
- **Python 3.9+**
- **Apple Silicon** (M1/M2/M3/M4) recommended, or Intel i5+
- **Camera** (USB webcam or built-in)
- **~1GB disk space**

### Windows
- **Windows** 10 or later
- **Python 3.9+**
- **CPU**: Intel i5 or AMD equivalent (modern multi-core recommended)
- **RAM**: 4GB minimum, 8GB+ recommended
- **Camera**: USB webcam or built-in camera
- **~1GB disk space**

## Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Complete installation instructions
- **[User Guide](docs/USAGE.md)** - How to use the application
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

## Project Structure

```
redzone-ai-monitor/
├── README.md                   # This file
├── LICENSE                     # MIT License
├── requirements_ai.txt         # Python dependencies
├── run_ai_app.py              # Main application entry point
├── ai_motion_app/             # Application source code
│   ├── main_app.py            # Main application
│   ├── camera_manager.py      # Camera handling
│   ├── ai_detector.py         # YOLO detection
│   ├── zone_manager.py        # Zone polygon logic
│   ├── alert_system.py        # Alert management
│   └── config.py              # Configuration
├── scripts/                    # Utility scripts
│   ├── setup_dependencies.sh  # macOS setup script
│   ├── setup_dependencies.ps1 # Windows PowerShell setup
│   ├── setup_dependencies.bat # Windows batch setup
│   └── ...
├── packaging/                  # Platform-specific packaging
│   ├── macos/                 # macOS packaging files
│   └── windows/               # Windows packaging files
├── docs/                       # Documentation
│   ├── INSTALLATION.md        # Installation guide
│   ├── USAGE.md               # User guide
│   └── TROUBLESHOOTING.md     # Troubleshooting
├── models/                     # AI model files
│   └── yolov8n.pt             # YOLOv8 nano model
├── zones/                      # Zone configuration
│   └── zone_config.json       # User settings
└── ...
```

## Keyboard Controls

| Key | Action |
|-----|--------|
| `D` | Enter zone drawing mode |
| `ENTER` | Finish drawing zone |
| `C` | Clear zone |
| `S` | Start monitoring |
| `P` | Pause/Resume |
| `Q` or `ESC` | Quit |

## License

MIT License - see [LICENSE](LICENSE) file for details.

**Important:** This software uses YOLOv8 from Ultralytics. Commercial use requires a separate commercial license from Ultralytics. See [LICENSE](LICENSE) for details.

## Credits

- **YOLOv8**: Ultralytics (https://github.com/ultralytics/ultralytics)
- **OpenCV**: Open Source Computer Vision Library
- **PyTorch**: Deep learning framework
