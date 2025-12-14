"""
Zone Mask Creator for Motion Detection App
Helps create zone mask images for area-specific detection
"""

import subprocess
import sys
from pathlib import Path


def create_simple_mask():
    """Create a simple mask template using ASCII art"""
    
    project_root = Path(__file__).parent
    zones_dir = project_root / "config" / "zones"
    zones_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("Zone Mask Creator")
    print("="*60)
    print()
    print("Zone masks define where motion detection should occur:")
    print("  • WHITE areas = motion detection ENABLED")
    print("  • BLACK areas = motion detection DISABLED")
    print()
    print("Steps to create a custom zone mask:")
    print()
    print("1. Start monitoring:")
    print("   python3 motion_app.py")
    print("   Click 'Start Monitoring' in menu bar")
    print()
    print("2. View camera feed:")
    print("   Open: http://localhost:8081")
    print()
    print("3. Take a screenshot of the camera view")
    print()
    print("4. Open screenshot in an image editor:")
    print("   • Preview (built-in)")
    print("   • GIMP (free)")
    print("   • Photoshop")
    print()
    print("5. Create a new layer and paint:")
    print("   • Paint WHITE on areas to DETECT motion")
    print("   • Paint BLACK on areas to IGNORE")
    print("   • Use the SAME resolution as camera (default: 640x480)")
    print()
    print("6. Export as PNG:")
    print(f"   Save to: {zones_dir}/mask.png")
    print()
    print("7. Update Motion configuration:")
    print("   Edit config/motion.conf and uncomment:")
    print(f"   mask_file {zones_dir}/mask.png")
    print()
    print("8. Restart monitoring to apply changes")
    print()
    
    # Offer to open zones directory
    print("-"*60)
    response = input("\nOpen zones directory in Finder? (y/n): ").strip().lower()
    
    if response == 'y':
        subprocess.run(['open', str(zones_dir)])
        print(f"\n✓ Opened: {zones_dir}")
    
    print()
    print("="*60)
    print("Example Mask Scenarios")
    print("="*60)
    print()
    print("Scenario 1: Monitor doorway only")
    print("  • Paint doorway area WHITE")
    print("  • Paint walls, windows, etc. BLACK")
    print()
    print("Scenario 2: Ignore tree in corner")
    print("  • Paint entire frame WHITE")
    print("  • Paint tree area BLACK")
    print()
    print("Scenario 3: Monitor specific zone")
    print("  • Paint rectangular zone WHITE")
    print("  • Paint everything else BLACK")
    print()
    
    print("Tips:")
    print("  • Use soft brushes for gradual transitions")
    print("  • Test and adjust as needed")
    print("  • Can use grayscale (darker = less sensitive)")
    print("  • Keep mask simple for better performance")
    print()


def check_existing_mask():
    """Check if a mask already exists"""
    
    project_root = Path(__file__).parent
    mask_file = project_root / "config" / "zones" / "mask.png"
    
    if mask_file.exists():
        print()
        print("="*60)
        print("✓ Existing Mask Found")
        print("="*60)
        print(f"\nLocation: {mask_file}")
        print()
        
        response = input("Open mask file? (y/n): ").strip().lower()
        if response == 'y':
            subprocess.run(['open', str(mask_file)])
            print(f"\n✓ Opened: {mask_file}")
        
        print()
        print("To create a new mask:")
        print(f"  1. Delete or rename: {mask_file}")
        print("  2. Follow the steps above to create a new one")
        print()
        
        return True
    
    return False


def test_mask_in_config():
    """Check if mask is referenced in config"""
    
    project_root = Path(__file__).parent
    config_file = project_root / "config" / "motion.conf"
    
    if not config_file.exists():
        print("\n⚠️  Warning: Configuration file not found")
        print("   Run: python3 scripts/create_config.py")
        return
    
    try:
        with open(config_file, 'r') as f:
            config_content = f.read()
        
        if 'mask_file' in config_content and not config_content.split('mask_file')[1].strip().startswith('#'):
            print("\n✓ Mask is configured in motion.conf")
            
            # Extract mask file path
            for line in config_content.split('\n'):
                if 'mask_file' in line and not line.strip().startswith('#'):
                    print(f"  {line.strip()}")
        else:
            print("\n⚠️  Mask not configured in motion.conf")
            print("\n   To enable mask:")
            print("   1. Edit config/motion.conf")
            print("   2. Find the line: # mask_file /path/to/mask.png")
            print("   3. Uncomment and set correct path")
            print("   4. Restart monitoring")
    
    except Exception as e:
        print(f"\n⚠️  Error reading config: {e}")


def main():
    """Main function"""
    
    # Check for existing mask
    mask_exists = check_existing_mask()
    
    if not mask_exists:
        # Show instructions for creating mask
        create_simple_mask()
    
    # Check configuration
    test_mask_in_config()
    
    print()
    print("="*60)
    print("Additional Resources")
    print("="*60)
    print()
    print("Motion mask documentation:")
    print("https://motion-project.github.io/motion_config.html#mask_file")
    print()
    print("Free image editors:")
    print("  • Preview (macOS built-in)")
    print("  • GIMP: https://www.gimp.org/")
    print("  • Paint.NET: https://www.getpaint.net/ (Windows)")
    print()


if __name__ == "__main__":
    main()


