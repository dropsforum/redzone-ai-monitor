@echo off
REM Build Windows executable for DROPS Red Zone Monitoring
REM This script must be run from the project root directory

setlocal enabledelayedexpansion

echo ========================================
echo Building Windows Executable
echo ========================================
echo.

REM Get the script directory and project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
cd /d "%PROJECT_ROOT%"

echo Current directory: %CD%
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run setup first:
    echo   scripts\setup_dependencies.bat
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo [1/4] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

REM Check if PyInstaller is installed
echo [2/4] Checking PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller!
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
) else (
    echo PyInstaller is installed.
)

echo.
echo [3/4] Building executable...
echo This may take several minutes...
echo.

REM Build the executable
pyinstaller packaging\windows\pyinstaller.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    echo.
    echo Check the error messages above for details.
    echo Common issues:
    echo   - Missing dependencies: Run scripts\setup_dependencies.bat
    echo   - PyInstaller errors: Check that all packages are installed
    echo   - Path issues: Make sure you're running from project root
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo.
echo [4/4] Verifying build...

if exist "dist\DROPS Red Zone Monitoring.exe" (
    echo.
    echo ========================================
    echo Build Complete!
    echo ========================================
    echo.
    echo Executable location: dist\DROPS Red Zone Monitoring.exe
    echo.
    dir "dist\DROPS Red Zone Monitoring.exe"
    echo.
    echo You can now run the executable directly!
    echo.
) else (
    echo [ERROR] Executable not found in dist folder!
    echo Build may have completed but executable is missing.
    echo Check the build output above for errors.
    echo.
)

echo Press any key to exit...
pause >nul
exit /b 0


