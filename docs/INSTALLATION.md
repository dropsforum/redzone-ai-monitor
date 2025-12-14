# Installation Guide

Complete installation guide for DROPS Red Zone Monitoring.

## Prerequisites

### macOS
- **macOS** 10.15 or later
- **Python 3.9+**
- Administrator access
- Camera (USB webcam or built-in)
- Internet connection (for initial setup)
- ~1GB free disk space

### Windows
- **Windows** 10 or later
- **Python 3.9+** (download from [python.org](https://www.python.org/downloads/))
- Administrator access (for some installations)
- Camera (USB webcam or built-in)
- Internet connection (for initial setup)
- ~1GB free disk space

## Quick Installation

### macOS Installation

#### Step 1: Install Homebrew

If you don't have Homebrew installed:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the prompts to add Homebrew to your PATH. After installation, verify:

```bash
brew --version
```

#### Step 2: Install Dependencies

```bash
cd /path/to/redzone-ai-monitor
chmod +x scripts/setup_dependencies.sh
./scripts/setup_dependencies.sh
```

This installs:
- FFmpeg and system libraries
- Python dependencies
- Creates virtual environment

**Expected time:** 10-15 minutes

#### Step 3: Run the Application

```bash
source venv/bin/activate
python3 run_ai_app.py
```

**First run:** YOLO will automatically download a 6MB model file (~10 seconds).

### Windows Installation

#### Step 1: Install Python

1. Download Python 3.9+ from [python.org](https://www.python.org/downloads/)
2. **Important:** During installation, check "Add Python to PATH"
3. Verify installation:
   ```cmd
   python --version
   ```

#### Step 2: Install Dependencies

**Option A: PowerShell (Recommended)**
```powershell
cd C:\path\to\redzone-ai-monitor
.\scripts\setup_dependencies.ps1
```

**Option B: Command Prompt**
```cmd
cd C:\path\to\redzone-ai-monitor
scripts\setup_dependencies.bat
```

This will:
- Create Python virtual environment
- Install all Python dependencies
- Verify installation

**Expected time:** 5-10 minutes

#### Step 3: Run the Application

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
python run_ai_app.py
```

**Command Prompt:**
```cmd
venv\Scripts\activate.bat
python run_ai_app.py
```

**First run:** YOLO will automatically download a 6MB model file (~10 seconds).

## Detailed Installation

### System Requirements

#### macOS
- **Minimum:** Intel i5 or M1, 4GB RAM
- **Recommended:** Apple Silicon (M1/M2/M3/M4), 8GB+ RAM
- **Performance:** Runs at 80-120 FPS on Apple Silicon

#### Windows
- **Minimum:** Intel i5 or AMD equivalent, 4GB RAM
- **Recommended:** Modern multi-core CPU, 8GB+ RAM
- **Performance:** Varies by hardware, typically 30-60 FPS on modern systems

### Camera Setup

The application will detect available cameras automatically. Supported cameras include:
- USB webcams (e.g., Logitech C920)
- Built-in cameras (MacBook, Studio Display, Windows laptops, etc.)

To check available cameras:

**macOS/Linux:**
```bash
python3 -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).read()[0]])"
```

**Windows:**
```cmd
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).read()[0]])"
```

### Virtual Environment

The setup script creates a virtual environment automatically. To activate manually:

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

### Verify Installation

Test the installation:

**macOS/Linux:**
```bash
python3 scripts/test_ai_performance.py
```

**Windows:**
```cmd
python scripts\test_ai_performance.py
```

This will:
1. Download YOLOv8 model (~6MB)
2. Benchmark system performance
3. Show expected FPS

## Building Distribution Package

### macOS

To create a standalone `.app` for distribution:

#### Prerequisites

```bash
pip install pyinstaller
```

#### Build

```bash
pyinstaller packaging/macos/pyinstaller.spec
```

The app will be at `dist/DROPS Red Zone Monitoring.app`.

#### Create DMG (Optional)

```bash
hdiutil create -volname DROPS-Red-Zone-Monitoring -srcfolder dist/"DROPS Red Zone Monitoring.app" -ov -format UDZO DROPS-Red-Zone-Monitoring-macos-arm64.dmg
```

### Windows

To create a standalone `.exe` for distribution:

#### Prerequisites

```cmd
pip install pyinstaller
```

#### Build

```cmd
packaging\windows\build_exe.bat
```

The executable will be at `dist\DROPS Red Zone Monitoring.exe`.

#### Create Installer (Optional)

Use NSIS or Inno Setup to create an installer package. See `packaging/windows/` for installer scripts.

## Troubleshooting Installation

### macOS Issues

#### Homebrew Installation Issues

If Homebrew installation fails:
1. Check internet connection
2. Ensure you have administrator privileges
3. Follow the error messages shown during installation

#### Python Dependencies Fail

If pip install fails:
```bash
python3 -m pip install --upgrade pip
source venv/bin/activate
pip install -r requirements_ai.txt
```

#### Camera Not Detected

1. Check camera connection
2. Grant camera permissions: System Settings > Privacy & Security > Camera
3. Restart the application

### Windows Issues

#### Python Not Found

If `python` command is not recognized:
1. Reinstall Python from [python.org](https://www.python.org/downloads/)
2. **Important:** Check "Add Python to PATH" during installation
3. Restart your terminal/command prompt after installation

#### PowerShell Execution Policy

If PowerShell script fails with execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Python Dependencies Fail

If pip install fails:
```cmd
python -m pip install --upgrade pip
venv\Scripts\activate.bat
pip install -r requirements_ai.txt
```

#### Camera Not Detected

1. Check camera connection
2. Grant camera permissions: Settings > Privacy > Camera
3. Ensure no other applications are using the camera
4. Restart the application

### Common Issues (Both Platforms)

#### Model Download Fails

If YOLO model download fails:
1. Check internet connection
2. The model will be downloaded automatically on first run
3. Model file location: `models/yolov8n.pt`

#### Virtual Environment Issues

If virtual environment activation fails:
- **macOS/Linux:** Ensure you're using `source venv/bin/activate`
- **Windows:** Use `venv\Scripts\activate.bat` (CMD) or `.\venv\Scripts\Activate.ps1` (PowerShell)

For more troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

