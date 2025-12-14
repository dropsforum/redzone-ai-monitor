"""
Platform Utilities for Cross-Platform Support
Provides unified API for platform-specific functionality
"""

import os
import sys
import platform
from pathlib import Path
from typing import Optional

# Platform detection
def get_platform() -> str:
    """Get the current platform name"""
    system = platform.system().lower()
    if system == 'darwin':
        return 'macos'
    elif system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    else:
        return 'unknown'

def is_windows() -> bool:
    """Check if running on Windows"""
    return get_platform() == 'windows'

def is_macos() -> bool:
    """Check if running on macOS"""
    return get_platform() == 'macos'

def is_linux() -> bool:
    """Check if running on Linux"""
    return get_platform() == 'linux'

# Platform-specific paths
def get_config_dir() -> Path:
    """Get platform-specific configuration directory"""
    if is_windows():
        # Windows: Use AppData\Local
        app_data = os.getenv('LOCALAPPDATA', os.path.expanduser('~/.local'))
        return Path(app_data) / 'DROPS Red Zone Monitoring'
    elif is_macos():
        # macOS: Use ~/Library/Application Support
        return Path.home() / 'Library' / 'Application Support' / 'DROPS Red Zone Monitoring'
    else:
        # Linux: Use ~/.config
        return Path.home() / '.config' / 'drops-redzone-monitoring'

def get_app_data_dir() -> Path:
    """Get platform-specific application data directory"""
    return get_config_dir()

# Platform-specific sound playback
def play_sound(sound_file: Optional[str] = None) -> bool:
    """
    Play a system sound cross-platform
    
    Args:
        sound_file: Path to sound file (optional, uses default system sound if None)
    
    Returns:
        True if sound played successfully, False otherwise
    """
    try:
        if sound_file and Path(sound_file).exists():
            # Use pygame for custom sound files (cross-platform)
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
                return True
            except Exception:
                pass
        
        # Platform-specific default sounds
        if is_windows():
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                return True
            except ImportError:
                # Fallback if winsound not available (shouldn't happen on Windows)
                pass
        elif is_macos():
            # Use afplay for macOS system sounds
            if sound_file:
                os.system(f'afplay "{sound_file}" &')
            else:
                os.system('afplay /System/Library/Sounds/Glass.aiff &')
            return True
        else:
            # Linux: Use aplay or pygame
            try:
                import pygame
                pygame.mixer.init()
                # Try to play a beep
                pygame.mixer.Sound.play(pygame.mixer.Sound(buffer=bytes([0] * 1000)))
                return True
            except Exception:
                # Fallback: try system beep
                os.system('echo -e "\a"')
                return True
    except Exception as e:
        print(f"Warning: Could not play sound: {e}")
        return False

def play_default_alert() -> bool:
    """Play the default alert sound for the platform"""
    if is_windows():
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            return True
        except ImportError:
            # Fallback if winsound not available (shouldn't happen on Windows)
            return play_sound()
    elif is_macos():
        os.system('afplay /System/Library/Sounds/Glass.aiff &')
        return True
    else:
        # Use pygame as fallback
        try:
            import pygame
            pygame.mixer.init()
            # Generate a simple beep
            import numpy as np
            sample_rate = 22050
            duration = 0.1
            frequency = 800
            t = np.linspace(0, duration, int(sample_rate * duration))
            wave = np.sin(2 * np.pi * frequency * t)
            wave = (wave * 32767).astype(np.int16)
            sound = pygame.sndarray.make_sound(wave)
            sound.play()
            return True
        except Exception:
            return play_sound()

# Platform-specific file operations
def get_executable_path() -> Path:
    """Get the path to the executable or script"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys.executable)
    else:
        # Running as script
        return Path(__file__).parent.parent / 'run_ai_app.py'

def get_project_root() -> Path:
    """Get the project root directory"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return Path(sys.executable).parent
    else:
        # Running as script
        return Path(__file__).parent.parent

# Platform-specific environment
def get_python_executable() -> str:
    """Get the Python executable name for the platform"""
    if is_windows():
        return 'python.exe'
    else:
        return 'python3'

def get_venv_activate_script() -> Path:
    """Get the virtual environment activation script path"""
    project_root = get_project_root()
    if is_windows():
        return project_root / 'venv' / 'Scripts' / 'activate.bat'
    else:
        return project_root / 'venv' / 'bin' / 'activate'

# Platform information
def get_platform_info() -> dict:
    """Get detailed platform information"""
    return {
        'platform': get_platform(),
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
    }

