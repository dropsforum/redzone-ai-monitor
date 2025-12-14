#!/bin/bash

# Launcher script for Motion Detection App

cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "Starting Motion Detection App..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found!${NC}"
    echo "Please run ./setup_dependencies.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if Motion is built
if [ ! -f "motion_install/bin/motion" ]; then
    echo -e "${YELLOW}Warning: Motion not built yet${NC}"
    echo "Please run ./build_motion.sh first"
    exit 1
fi

# Check if config exists
if [ ! -f "config/motion.conf" ]; then
    echo -e "${YELLOW}Warning: Configuration not found${NC}"
    echo "Creating default configuration..."
    python3 scripts/create_config.py
    echo ""
fi

# Run the app
echo -e "${GREEN}Launching Motion Detection App...${NC}"
echo "Look for the app icon in your menu bar!"
echo ""
python3 motion_app.py


