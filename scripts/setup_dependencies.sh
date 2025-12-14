#!/bin/bash

# Setup script for Motion Detection Mac App
# This script installs all required dependencies for building and running Motion

set -e  # Exit on error

echo "================================================"
echo "Motion Detection App - Dependency Setup"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}Error: This script is for macOS only${NC}"
    exit 1
fi

# Check if Homebrew is installed
echo -e "${YELLOW}Checking for Homebrew...${NC}"
if ! command -v brew &> /dev/null; then
    echo -e "${RED}Homebrew is not installed!${NC}"
    echo ""
    echo "Please install Homebrew first by running:"
    echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    echo ""
    echo "After installation, add Homebrew to your PATH and run this script again."
    exit 1
fi

echo -e "${GREEN}✓ Homebrew found${NC}"
echo ""

# Update Homebrew
echo -e "${YELLOW}Updating Homebrew...${NC}"
brew update

# Install required packages
echo ""
echo -e "${YELLOW}Installing Motion dependencies...${NC}"
brew install ffmpeg pkg-config libjpeg libmicrohttpd automake autoconf libtool gettext

echo ""
echo -e "${GREEN}✓ System dependencies installed${NC}"
echo ""

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}Installing Python 3...${NC}"
    brew install python3
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment and install requirements
echo -e "${YELLOW}Installing Python packages...${NC}"
source venv/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements.txt

echo ""
echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# Set up directory structure
echo -e "${YELLOW}Creating directory structure...${NC}"
mkdir -p config
mkdir -p config/zones
mkdir -p logs
mkdir -p captures
mkdir -p motion_build

echo -e "${GREEN}✓ Directory structure created${NC}"
echo ""

# Export PATH for gettext (required for Motion build)
export PATH="/usr/local/opt/gettext/bin:/usr/local/bin:/opt/homebrew/opt/gettext/bin:/opt/homebrew/bin:$PATH"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Dependencies installation complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Next steps:"
echo "1. Run: ./build_motion.sh (to build Motion from source)"
echo "2. Run: python3 test_camera.py (to test camera detection)"
echo "3. Run: python3 motion_app.py (to start the menu bar app)"
echo ""


