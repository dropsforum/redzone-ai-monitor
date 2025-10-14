#!/bin/bash

# Start FFmpeg RTSP server for Logitech C920 camera
# This streams the camera so Motion can access it

echo "Starting camera stream from Logitech C920..."
echo "This will make the camera available at: rtsp://localhost:8554/camera"
echo ""

# Install mediamtx if not already installed
if ! command -v mediamtx &> /dev/null; then
    echo "Installing mediamtx (RTSP server)..."
    brew install mediamtx
fi

# Start mediamtx RTSP server in background
echo "Starting RTSP server..."
mediamtx &
MEDIAMTX_PID=$!
echo "RTSP server started (PID: $MEDIAMTX_PID)"

# Wait for server to start
sleep 2

# Stream camera to RTSP server using FFmpeg
echo "Streaming Logitech C920 to RTSP..."
/opt/homebrew/bin/ffmpeg \
    -f avfoundation \
    -framerate 15 \
    -video_size 640x480 \
    -i "0" \
    -c:v libx264 \
    -preset ultrafast \
    -tune zerolatency \
    -f rtsp \
    rtsp://localhost:8554/camera

# Cleanup on exit
kill $MEDIAMTX_PID 2>/dev/null


