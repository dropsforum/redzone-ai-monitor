#!/usr/bin/env python3
"""
Launcher script for DROPS Red Zone Monitoring
"""

import sys
import os
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from ai_motion_app.main_app import MotionDetectionApp

def main():
    """Run the application"""
    try:
        app = MotionDetectionApp()
        app.run()
    except Exception as e:
        print(f"\n✗ Error running application: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())


