"""
Camera Detection and Testing Utility
Helps identify available cameras and test Motion configuration
"""

import subprocess
import sys
from pathlib import Path


def check_camera_devices():
    """Check for available camera devices on macOS"""
    print("Checking for camera devices...\n")
    
    # On macOS, we need to use system_profiler to list cameras
    try:
        result = subprocess.run(
            ['system_profiler', 'SPCameraDataType'],
            capture_output=True,
            text=True,
            check=True
        )
        
        output = result.stdout
        
        if 'No video capture devices' in output or not output.strip():
            print("❌ No cameras detected!")
            print("\nMake sure:")
            print("  1. Your camera is connected")
            print("  2. Camera permissions are granted")
            print("  3. No other app is using the camera")
            return False
        
        print("✓ Camera(s) detected:\n")
        print(output)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error checking cameras: {e}")
        return False
    except FileNotFoundError:
        print("Error: system_profiler not found (are you on macOS?)")
        return False


def check_video_devices():
    """Check for /dev/video* devices (used by Motion)"""
    print("\nChecking for /dev/video* devices...")
    
    # On macOS, video devices might not appear as /dev/video*
    # Motion on macOS typically uses AVFoundation or other frameworks
    
    result = subprocess.run(
        ['ls', '-la', '/dev/video*'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✓ Video devices found:")
        print(result.stdout)
        return True
    else:
        print("ℹ️  No /dev/video* devices found")
        print("   (This is normal on macOS - Motion will use AVFoundation)")
        return True  # Not an error on macOS


def check_motion_build():
    """Check if Motion is built and ready"""
    print("\nChecking Motion installation...\n")
    
    project_root = Path(__file__).parent
    # Motion installed in home directory to avoid path with spaces issues
    import os
    motion_binary = Path(os.path.expanduser("~/.motion_install")) / "bin" / "motion"
    
    if not motion_binary.exists():
        print("❌ Motion not found!")
        print(f"   Expected location: {motion_binary}")
        print("\nPlease run: ./build_motion.sh")
        return False
    
    print(f"✓ Motion found: {motion_binary}")
    
    # Check Motion version
    try:
        result = subprocess.run(
            [str(motion_binary), '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        version_info = result.stderr + result.stdout
        if version_info:
            print(f"\nMotion version info:")
            print(version_info[:500])  # Print first 500 chars
    except Exception as e:
        print(f"Warning: Could not get Motion version: {e}")
    
    return True


def check_config():
    """Check if Motion configuration exists"""
    print("\nChecking Motion configuration...\n")
    
    project_root = Path(__file__).parent
    config_file = project_root / "config" / "motion.conf"
    
    if not config_file.exists():
        print("❌ Motion configuration not found!")
        print(f"   Expected location: {config_file}")
        print("\nPlease create config/motion.conf")
        print("You can use: python3 create_config.py")
        return False
    
    print(f"✓ Configuration found: {config_file}")
    
    # Check for key configuration parameters
    try:
        with open(config_file, 'r') as f:
            config_content = f.read()
        
        important_params = [
            'target_dir',
            'stream_port',
            'webcontrol_port'
        ]
        
        print("\nKey configuration parameters:")
        for param in important_params:
            if param in config_content:
                print(f"  ✓ {param} configured")
            else:
                print(f"  ⚠️  {param} not found")
        
    except Exception as e:
        print(f"Warning: Could not read config: {e}")
    
    return True


def check_dependencies():
    """Check Python dependencies"""
    print("\nChecking Python dependencies...\n")
    
    required_modules = [
        'rumps',
        'watchdog',
        'psutil',
        'requests'
    ]
    
    all_present = True
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError:
            print(f"  ❌ {module} - NOT INSTALLED")
            all_present = False
    
    if not all_present:
        print("\nPlease install missing dependencies:")
        print("  source venv/bin/activate")
        print("  pip3 install -r requirements.txt")
        return False
    
    print("\n✓ All Python dependencies installed")
    return True


def main():
    """Run all checks"""
    print("="*60)
    print("Motion Detection App - System Check")
    print("="*60)
    print()
    
    checks = [
        ("Camera Devices", check_camera_devices),
        ("Video Device Support", check_video_devices),
        ("Motion Build", check_motion_build),
        ("Motion Configuration", check_config),
        ("Python Dependencies", check_dependencies)
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n❌ Error during {check_name}: {e}")
            results.append((check_name, False))
        
        print("\n" + "-"*60 + "\n")
    
    # Summary
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print()
    
    all_passed = True
    for check_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {check_name}")
        if not result:
            all_passed = False
    
    print()
    
    if all_passed:
        print("✓ All checks passed! You're ready to use the Motion Detection App.")
        print("\nNext steps:")
        print("  1. Run: python3 motion_app.py")
        print("  2. Click the app icon in your menu bar")
        print("  3. Select 'Start Monitoring'")
    else:
        print("⚠️  Some checks failed. Please address the issues above.")
        print("\nCommon fixes:")
        print("  1. Run: ./setup_dependencies.sh (to install dependencies)")
        print("  2. Run: ./build_motion.sh (to build Motion)")
        print("  3. Run: python3 create_config.py (to create configuration)")
    
    print()
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

