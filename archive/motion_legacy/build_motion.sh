#!/bin/bash

# Script to clone and build Motion from source

set -e  # Exit on error

echo "================================================"
echo "Building Motion from Source"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set up PATH for gettext and other Homebrew packages
if [ -d "/opt/homebrew/bin" ]; then
    # Apple Silicon Mac
    export PATH="/opt/homebrew/opt/gettext/bin:/opt/homebrew/bin:$PATH"
    export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
elif [ -d "/usr/local/bin" ]; then
    # Intel Mac
    export PATH="/usr/local/opt/gettext/bin:/usr/local/bin:$PATH"
    export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"
fi

# Check if motion_build directory exists
if [ ! -d "motion_build" ]; then
    echo -e "${YELLOW}Cloning Motion repository...${NC}"
    git clone https://github.com/Motion-Project/motion.git motion_build
    echo -e "${GREEN}✓ Motion repository cloned${NC}"
else
    echo -e "${YELLOW}Motion repository already exists, pulling latest changes...${NC}"
    cd motion_build
    git pull
    cd ..
    echo -e "${GREEN}✓ Motion repository updated${NC}"
fi

echo ""

# Navigate to motion directory
cd motion_build

# Clean previous builds
if [ -f "Makefile" ]; then
    echo -e "${YELLOW}Cleaning previous build...${NC}"
    make clean || true
fi

echo ""
echo -e "${YELLOW}Running autoreconf...${NC}"
autoreconf -fiv

echo ""
echo -e "${YELLOW}Configuring Motion build...${NC}"
# Use $HOME to avoid path with spaces issues
INSTALL_DIR="$HOME/.motion_install"
./configure --prefix="$INSTALL_DIR"

echo ""
echo -e "${YELLOW}Building Motion (this may take several minutes)...${NC}"
make

echo ""
echo -e "${YELLOW}Installing Motion to local directory...${NC}"
make install

# Go back to project root
cd ..

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Motion build complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Motion installed to: $(pwd)/motion_install/bin/motion"
echo ""
echo "Next steps:"
echo "1. Run: python3 test_camera.py (to test camera detection)"
echo "2. Run: python3 motion_app.py (to start the menu bar app)"
echo ""

