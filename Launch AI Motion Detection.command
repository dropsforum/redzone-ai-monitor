#!/bin/bash
# AI Motion Detection App Launcher
# Double-click this file to start the application

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate Python virtual environment
source venv/bin/activate

# Clear screen for clean start
clear

echo "======================================"
echo "  DROPS Red Zone Monitoring POC"
echo "======================================"
echo ""
echo "Starting application..."
echo ""

# Run the application
python3 run_ai_app.py

# Keep terminal open after app closes
echo ""
echo "======================================"
echo "Application closed."
echo "======================================"
echo ""
echo "Press any key to close this window..."
read -n 1 -s


