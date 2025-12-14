@echo off
REM Batch script for Windows dependency setup (fallback if PowerShell not available)
REM DROPS Red Zone Monitoring - Windows Setup
REM This script must be run from the project root directory

setlocal enabledelayedexpansion

echo ========================================
echo DROPS Red Zone Monitoring - Windows Setup
echo ========================================
echo.

REM Get the script directory and project root
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

echo Current directory: %CD%
echo.

REM Check Python installation
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.9+ from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: During installation, check "Add Python to PATH"
    echo After installation, restart this command prompt.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

python --version
echo Python found!
echo.

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%
echo.

REM Create virtual environment
echo [2/5] Setting up virtual environment...
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        echo.
        echo Make sure Python is properly installed and accessible.
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
)

echo.

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    echo.
    echo Try deleting the venv folder and running this script again.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

REM Upgrade pip
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [WARNING] Failed to upgrade pip, continuing anyway...
)

REM Install dependencies
echo.
echo [5/5] Installing Python dependencies...
echo This may take 5-10 minutes...
echo.

pip install -r requirements_ai.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install some dependencies!
    echo.
    echo Common solutions:
    echo   1. Check your internet connection
    echo   2. Try: pip install --upgrade pip
    echo   3. Try installing packages individually from requirements_ai.txt
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To run the application:
echo   1. Activate virtual environment:
echo      venv\Scripts\activate.bat
echo.
echo   2. Run the application:
echo      python run_ai_app.py
echo.
echo To build Windows executable:
echo   packaging\windows\build_exe.bat
echo.
echo Press any key to exit...
pause >nul
exit /b 0


