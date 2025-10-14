#!/bin/bash

# Script to create a distributable installer package for Motion Detection App

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "="*60
echo "Creating Motion Detection App Installer"
echo "="*60
echo ""

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
APP_NAME="MotionDetector"
VERSION="1.0.0"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if [ ! -d "venv" ]; then
    echo -e "${RED}Error: Virtual environment not found${NC}"
    echo "Run ./setup_dependencies.sh first"
    exit 1
fi

if [ ! -f "motion_install/bin/motion" ]; then
    echo -e "${RED}Error: Motion not built${NC}"
    echo "Run ./build_motion.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo -e "${YELLOW}Installing PyInstaller...${NC}"
    pip3 install pyinstaller
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Create dist directory
mkdir -p "$DIST_DIR"
mkdir -p "$DIST_DIR/app_bundle"

# Bundle Python app with PyInstaller
echo -e "${YELLOW}Bundling Python application...${NC}"

pyinstaller --noconfirm \
    --name="$APP_NAME" \
    --windowed \
    --osx-bundle-identifier="com.motiondetector.app" \
    --hidden-import=rumps \
    --hidden-import=watchdog \
    --hidden-import=psutil \
    --hidden-import=requests \
    --add-data="motion_install:motion_install" \
    --add-data="config:config" \
    --add-data="scripts:scripts" \
    motion_app.py

echo -e "${GREEN}✓ App bundled${NC}"
echo ""

# Copy additional files
echo -e "${YELLOW}Copying additional files...${NC}"

cp -r dist/$APP_NAME.app "$DIST_DIR/app_bundle/"
cp README.md "$DIST_DIR/app_bundle/"
cp QUICKSTART.md "$DIST_DIR/app_bundle/"

# Create a post-install script
cat > "$DIST_DIR/app_bundle/setup.sh" << 'EOF'
#!/bin/bash

echo "Setting up Motion Detection App..."

# Create necessary directories
mkdir -p ~/MotionDetector/captures
mkdir -p ~/MotionDetector/logs
mkdir -p ~/MotionDetector/config

# Copy configuration template if doesn't exist
if [ ! -f ~/MotionDetector/config/motion.conf ]; then
    cp config/motion.conf ~/MotionDetector/config/
fi

echo "✓ Setup complete!"
echo ""
echo "To run the app:"
echo "1. Open the MotionDetector app from Applications"
echo "2. Grant camera permissions when prompted"
echo "3. Click the menu bar icon to start monitoring"
EOF

chmod +x "$DIST_DIR/app_bundle/setup.sh"

echo -e "${GREEN}✓ Files copied${NC}"
echo ""

# Create DMG installer
echo -e "${YELLOW}Creating DMG installer...${NC}"

DMG_NAME="MotionDetector-v${VERSION}.dmg"
DMG_PATH="$DIST_DIR/$DMG_NAME"

# Remove old DMG if exists
[ -f "$DMG_PATH" ] && rm "$DMG_PATH"

# Create DMG
hdiutil create \
    -volname "Motion Detector" \
    -srcfolder "$DIST_DIR/app_bundle" \
    -ov \
    -format UDZO \
    "$DMG_PATH"

echo -e "${GREEN}✓ DMG created${NC}"
echo ""

# Create PKG installer (alternative)
echo -e "${YELLOW}Creating PKG installer...${NC}"

PKG_NAME="MotionDetector-v${VERSION}.pkg"
PKG_PATH="$DIST_DIR/$PKG_NAME"

# Build package structure
mkdir -p "$DIST_DIR/pkg_root/Applications"
cp -r dist/$APP_NAME.app "$DIST_DIR/pkg_root/Applications/"

# Create package
pkgbuild \
    --root "$DIST_DIR/pkg_root" \
    --identifier "com.motiondetector.app" \
    --version "$VERSION" \
    --install-location "/" \
    "$PKG_PATH"

echo -e "${GREEN}✓ PKG created${NC}"
echo ""

# Summary
echo "="*60
echo -e "${GREEN}Installer Creation Complete!${NC}"
echo "="*60
echo ""
echo "Distribution packages created:"
echo "  • DMG: $DMG_PATH"
echo "  • PKG: $PKG_PATH"
echo ""
echo "To install on another Mac:"
echo "  1. Copy the DMG or PKG file to the target Mac"
echo "  2. Open the DMG and drag app to Applications"
echo "     OR install the PKG file"
echo "  3. Run the setup.sh script in the app directory"
echo "  4. Launch the app from Applications"
echo ""
echo "Note: The target Mac must have:"
echo "  • macOS 10.15 or later"
echo "  • Camera connected"
echo "  • Homebrew (for dependencies)"
echo ""


