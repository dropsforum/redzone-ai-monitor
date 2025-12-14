# Windows Build Instructions

## Easiest option (no local setup): GitHub builds it for you

If your code is on GitHub, you can generate the Windows `.exe` without installing anything on your Windows machine:

1. Push your latest code to GitHub
2. On GitHub, open your repository and click **Actions**
3. Click **Build Windows EXE**
4. Click **Run workflow**
5. After it finishes, download the artifact **DROPS-Red-Zone-Monitoring-Windows** and unzip it
6. Run `DROPS Red Zone Monitoring.exe`

## Quick Build

1. **Open Command Prompt** (not PowerShell) in the project root directory
2. **Run the build script:**
   ```cmd
   packaging\windows\build_exe.bat
   ```

## Troubleshooting

### Script Closes Immediately

If the script window closes before you can see errors:

1. **Open Command Prompt manually:**
   - Press `Win + R`
   - Type `cmd` and press Enter
   - Navigate to project directory:
     ```cmd
     cd C:\path\to\redzone-ai-monitor
     ```
   - Run the script:
     ```cmd
     packaging\windows\build_exe.bat
     ```

2. **Or run from PowerShell with pause:**
   ```powershell
   cmd /c "packaging\windows\build_exe.bat && pause"
   ```

### Common Errors

#### "Virtual environment not found"
**Solution:** Run setup first:
```cmd
scripts\setup_dependencies.bat
```

#### "Python not found"
**Solution:** 
1. Install Python 3.9+ from [python.org](https://www.python.org/downloads/)
2. **Important:** Check "Add Python to PATH" during installation
3. Restart Command Prompt after installation

#### "PyInstaller not found"
**Solution:** The script will try to install it automatically. If it fails:
```cmd
venv\Scripts\activate.bat
pip install pyinstaller
```

#### Build Fails with Import Errors
**Solution:** Make sure all dependencies are installed:
```cmd
venv\Scripts\activate.bat
pip install -r requirements_ai.txt
```

## Manual Build

If the batch script doesn't work, build manually:

```cmd
REM 1. Activate virtual environment
venv\Scripts\activate.bat

REM 2. Install PyInstaller (if not installed)
pip install pyinstaller

REM 3. Build executable
pyinstaller packaging\windows\pyinstaller.spec --clean --noconfirm

REM 4. Check result
dir dist\DROPS Red Zone Monitoring.exe
```

## Output Location

The executable will be created at:
```
dist\DROPS Red Zone Monitoring.exe
```

## Testing the Executable

1. Navigate to `dist` folder
2. Double-click `DROPS Red Zone Monitoring.exe`
3. If Windows shows security warning, click "More info" → "Run anyway"

## Notes

- The build process takes 5-15 minutes depending on your system
- The executable will be ~200-300 MB (includes all dependencies)
- First run may be slower as Windows indexes the executable
- Camera permissions may need to be granted on first run

