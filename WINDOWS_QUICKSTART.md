# Windows Quick Start Guide

Quick start guide for Windows users.

## Prerequisites

- Windows 10 or later
- Python 3.9+ ([Download](https://www.python.org/downloads/))
- Camera (USB webcam or built-in)

## Installation

### Step 1: Install Python

1. Download Python 3.9+ from [python.org](https://www.python.org/downloads/)
2. **Important:** During installation, check "Add Python to PATH"
3. Verify installation:
   ```cmd
   python --version
   ```

### Step 2: Setup Application

**PowerShell (Recommended):**
```powershell
cd C:\path\to\redzone-ai-monitor
.\scripts\setup_dependencies.ps1
```

**Command Prompt:**
```cmd
cd C:\path\to\redzone-ai-monitor
scripts\setup_dependencies.bat
```

### Step 3: Run Application

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

## Using the Application

1. **Draw Zone:** Press `D`, click points to draw polygon, press `ENTER`
2. **Start Monitoring:** Press `S`
3. **Pause/Resume:** Press `P`
4. **Clear Zone:** Press `C`
5. **Quit:** Press `Q` or `ESC`

## Building Windows Executable

### Easiest option (recommended): GitHub builds it for you

If your code is on GitHub, you can generate the Windows `.exe` without setting up a build environment:

1. Push your latest code to GitHub
2. On GitHub, open your repository and click **Actions**
3. Click **Build Windows EXE**
4. Click **Run workflow**
5. Download the artifact **DROPS-Red-Zone-Monitoring-Windows** and unzip it
6. Run `DROPS Red Zone Monitoring.exe`

### Build it locally on Windows

To create a standalone `.exe`:

```cmd
packaging\windows\build_exe.bat
```

The executable will be at `dist\DROPS Red Zone Monitoring.exe`.

## Troubleshooting

### PowerShell Execution Policy Error

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Camera Not Detected

1. Check Device Manager for camera
2. Update camera drivers if needed
3. Close other applications using camera
4. Grant camera permissions in Windows Settings

### Python Not Found

1. Reinstall Python with "Add Python to PATH" checked
2. Restart command prompt after installation

For more help, see [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).


