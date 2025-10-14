"""
Configuration Generator for Motion Detection App
Creates a Motion configuration file with sensible defaults for macOS
"""

import os
from pathlib import Path


def create_motion_config():
    """Create Motion configuration file"""
    
    project_root = Path(__file__).parent
    config_dir = project_root / "config"
    config_file = config_dir / "motion.conf"
    captures_dir = project_root / "captures"
    logs_dir = project_root / "logs"
    
    # Create directories
    config_dir.mkdir(exist_ok=True)
    captures_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)
    
    # Configuration template
    config_content = f"""############################################################
# Motion Detection Configuration
# Generated for Motion Detection Mac App
############################################################

# System Settings
############################################################

# Run in daemon mode (background)
daemon off

# Process ID file
process_id_file {logs_dir}/motion.pid

# Log file and level
log_file {logs_dir}/motion.log
log_level 6
log_type all

# Camera Settings
############################################################

# Camera device
# On macOS, Motion will auto-detect the camera
# If you have multiple cameras, you may need to specify:
# video_device /dev/video0
videodevice /dev/video0

# Camera input (default: -1 for auto-detect)
input -1

# Video norm (default: 0 for auto)
norm 0

# Image width and height (adjust based on your camera)
width 640
height 480

# Frames per second
framerate 15

# Rotate image (0, 90, 180, 270)
rotate 0

# Motion Detection Settings
############################################################

# Threshold for motion detection (1-65535)
# Lower = more sensitive
# Recommended: 1500-4500
threshold 2500

# Minimum number of frames with motion
minimum_motion_frames 2

# Event gap (seconds between events)
event_gap 10

# Pre-capture frames (frames before motion)
pre_capture 3

# Post-capture frames (frames after motion)
post_capture 5

# Maximum length of movie (seconds, 0 = unlimited)
max_movie_time 60

# Output Settings
############################################################

# Target directory for images and movies
target_dir {captures_dir}

# Image file name
picture_filename %Y%m%d_%H%M%S_%v-%q

# Snapshot interval (0 = disabled)
snapshot_interval 0

# Movie output settings
picture_output on
picture_output_motion on

# Movie format (mp4, avi, mov, mkv, hevc)
movie_output on
movie_output_motion off
movie_filename %Y%m%d_%H%M%S_%v
movie_codec mp4

# Movie quality (1-100, higher = better)
movie_quality 75

# Web Interface Settings
############################################################

# Enable web control interface
webcontrol_port 8080
webcontrol_localhost off

# Enable live stream
stream_port 8081
stream_localhost off

# Stream quality (1-100)
stream_quality 80

# Maximum framerate for stream
stream_maxrate 15

# Authentication (uncomment and set username/password if needed)
# webcontrol_authentication username:password
# stream_authentication username:password

# Event Scripts
############################################################

# Script to run when motion is detected
# This can be used to trigger custom notifications
on_event_start {project_root}/scripts/on_motion_start.sh %Y %m %d %H %M %S

# Script to run when motion ends
on_event_end {project_root}/scripts/on_motion_end.sh %Y %m %d %H %M %S

# Script to run when picture is saved
on_picture_save {project_root}/scripts/on_picture_save.sh %f

# Script to run when movie is created
on_movie_end {project_root}/scripts/on_movie_end.sh %f

# Zone Detection (Area Mask)
############################################################

# To configure zone-based detection:
# 1. Create a mask image (black/white PNG)
#    - White areas: motion detection enabled
#    - Black areas: motion detection disabled
# 2. Save as config/zones/mask.png
# 3. Uncomment and set:
# mask_file {config_dir}/zones/mask.png

# Privacy mask (always exclude certain areas)
# mask_privacy {config_dir}/zones/privacy_mask.png

# Text overlay on images
############################################################

# Enable text overlay
text_left Motion Detected
text_right %Y-%m-%d %H:%M:%S

# Text scale (1-10)
text_scale 2

# Advanced Settings
############################################################

# Noise level (for auto-threshold)
noise_level 32

# Noise tuning
noise_tune on

# Despeckle filter (prevent false positives)
despeckle_filter EedDl

# Lightswitch threshold (0-100, 0 = disabled)
# Prevents false positives from sudden lighting changes
lightswitch_percent 5

# Minimum area of motion
area_detect 500

# Smart mask speed (0-10, 0 = disabled)
# Learns static areas and excludes them
smart_mask_speed 0

# Performance
############################################################

# Picture quality (1-100)
picture_quality 85

# Enable/disable features for performance
emulate_motion off

############################################################
# End of configuration
############################################################
"""
    
    # Write configuration file
    try:
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        print(f"✓ Motion configuration created: {config_file}")
        print()
        print("Configuration highlights:")
        print(f"  • Captures directory: {captures_dir}")
        print(f"  • Web interface: http://localhost:8080")
        print(f"  • Live stream: http://localhost:8081")
        print(f"  • Motion threshold: 2500 (adjust if needed)")
        print()
        print("Next steps:")
        print("  1. Review and customize config/motion.conf if needed")
        print("  2. Run: python3 test_camera.py (to verify setup)")
        print("  3. Run: python3 motion_app.py (to start the app)")
        print()
        print("To configure zone-based detection:")
        print("  1. Start the app and view the camera feed")
        print("  2. Create a mask image (white = detect, black = ignore)")
        print("  3. Save as config/zones/mask.png")
        print("  4. Uncomment 'mask_file' in config/motion.conf")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating configuration: {e}")
        return False


def create_event_scripts():
    """Create event handler scripts"""
    
    project_root = Path(__file__).parent
    scripts_dir = project_root / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    
    # Create on_motion_start.sh
    start_script = scripts_dir / "on_motion_start.sh"
    start_script_content = """#!/bin/bash
# Script executed when motion is detected
# Parameters: year month day hour minute second

YEAR=$1
MONTH=$2
DAY=$3
HOUR=$4
MINUTE=$5
SECOND=$6

TIMESTAMP="${YEAR}-${MONTH}-${DAY} ${HOUR}:${MINUTE}:${SECOND}"

# Log the event
echo "Motion detected at ${TIMESTAMP}" >> logs/events.log

# Create event flag file for event listener
echo "${TIMESTAMP}" > logs/motion_event.flag
"""
    
    # Create on_motion_end.sh
    end_script = scripts_dir / "on_motion_end.sh"
    end_script_content = """#!/bin/bash
# Script executed when motion ends
# Parameters: year month day hour minute second

YEAR=$1
MONTH=$2
DAY=$3
HOUR=$4
MINUTE=$5
SECOND=$6

TIMESTAMP="${YEAR}-${MONTH}-${DAY} ${HOUR}:${MINUTE}:${SECOND}"

# Log the event
echo "Motion ended at ${TIMESTAMP}" >> logs/events.log
"""
    
    # Create on_picture_save.sh
    picture_script = scripts_dir / "on_picture_save.sh"
    picture_script_content = """#!/bin/bash
# Script executed when a picture is saved
# Parameters: filename

FILENAME=$1

# Log the event
echo "Picture saved: ${FILENAME}" >> logs/events.log
"""
    
    # Create on_movie_end.sh
    movie_script = scripts_dir / "on_movie_end.sh"
    movie_script_content = """#!/bin/bash
# Script executed when a movie is completed
# Parameters: filename

FILENAME=$1

# Log the event
echo "Movie saved: ${FILENAME}" >> logs/events.log
"""
    
    # Write all scripts
    scripts = [
        (start_script, start_script_content),
        (end_script, end_script_content),
        (picture_script, picture_script_content),
        (movie_script, movie_script_content)
    ]
    
    try:
        for script_file, content in scripts:
            with open(script_file, 'w') as f:
                f.write(content)
            
            # Make scripts executable
            os.chmod(script_file, 0o755)
        
        print(f"✓ Event scripts created in: {scripts_dir}")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating event scripts: {e}")
        return False


def main():
    """Create configuration and scripts"""
    print("="*60)
    print("Motion Detection App - Configuration Generator")
    print("="*60)
    print()
    
    success = True
    
    if not create_motion_config():
        success = False
    
    print()
    
    if not create_event_scripts():
        success = False
    
    if success:
        print()
        print("="*60)
        print("✓ Configuration setup complete!")
        print("="*60)
    
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())


