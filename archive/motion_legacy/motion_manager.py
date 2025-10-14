"""
Motion Manager for Motion Detection App
Manages the Motion process lifecycle (start, stop, status)
"""

import subprocess
import os
import signal
import time
import psutil
from pathlib import Path


class MotionManager:
    """Manage the Motion detection software process"""
    
    def __init__(self, project_root=None):
        """
        Initialize Motion Manager
        
        Args:
            project_root (str): Root directory of the project
        """
        if project_root is None:
            project_root = Path(__file__).parent
        else:
            project_root = Path(project_root)
        
        self.project_root = project_root
        # Motion binary installed in home directory to avoid path with spaces issues
        import os
        self.motion_binary = Path(os.path.expanduser("~/.motion_install")) / "bin" / "motion"
        self.config_file = project_root / "config" / "motion.conf"
        self.pid_file = project_root / "logs" / "motion.pid"
        self.log_file = project_root / "logs" / "motion.log"
        self.process = None
        
        # Ensure directories exist
        (project_root / "logs").mkdir(exist_ok=True)
        (project_root / "captures").mkdir(exist_ok=True)
    
    def is_motion_installed(self):
        """Check if Motion binary exists"""
        return self.motion_binary.exists()
    
    def is_config_ready(self):
        """Check if Motion configuration file exists"""
        return self.config_file.exists()
    
    def is_running(self):
        """
        Check if Motion process is running
        
        Returns:
            bool: True if Motion is running, False otherwise
        """
        # Check if PID file exists and process is alive
        if self.pid_file.exists():
            try:
                with open(self.pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process with this PID exists and is motion
                if psutil.pid_exists(pid):
                    proc = psutil.Process(pid)
                    if 'motion' in proc.name().lower():
                        return True
            except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Also check by process name as fallback
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'motion' in proc.info['name'].lower():
                    # Check if it's our motion instance
                    if proc.info['cmdline'] and str(self.config_file) in ' '.join(proc.info['cmdline']):
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, TypeError):
                continue
        
        return False
    
    def get_motion_pid(self):
        """Get the PID of the running Motion process"""
        if self.pid_file.exists():
            try:
                with open(self.pid_file, 'r') as f:
                    return int(f.read().strip())
            except (ValueError, FileNotFoundError):
                pass
        return None
    
    def start(self):
        """
        Start the Motion detection process
        
        Returns:
            tuple: (success: bool, message: str)
        """
        # Check if already running
        if self.is_running():
            return False, "Motion is already running"
        
        # Check if Motion is installed
        if not self.is_motion_installed():
            return False, f"Motion binary not found at {self.motion_binary}. Please run build_motion.sh first."
        
        # Check if config exists
        if not self.is_config_ready():
            return False, f"Configuration file not found at {self.config_file}. Please create it first."
        
        try:
            # Open log file for output
            log_handle = open(self.log_file, 'a')
            
            # Start Motion process
            self.process = subprocess.Popen(
                [str(self.motion_binary), '-c', str(self.config_file)],
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            
            # Wait a moment and check if it started successfully
            time.sleep(2)
            
            if self.process.poll() is not None:
                # Process already terminated
                log_handle.close()
                return False, f"Motion failed to start. Check log: {self.log_file}"
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(self.process.pid))
            
            print(f"✓ Motion started with PID {self.process.pid}")
            return True, "Motion started successfully"
            
        except FileNotFoundError:
            return False, f"Motion binary not found: {self.motion_binary}"
        except Exception as e:
            return False, f"Error starting Motion: {str(e)}"
    
    def stop(self):
        """
        Stop the Motion detection process
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_running():
            # Clean up PID file if it exists
            if self.pid_file.exists():
                self.pid_file.unlink()
            return False, "Motion is not running"
        
        try:
            pid = self.get_motion_pid()
            if pid:
                # Send SIGTERM for graceful shutdown
                os.kill(pid, signal.SIGTERM)
                
                # Wait for process to terminate
                for _ in range(10):  # Wait up to 5 seconds
                    if not self.is_running():
                        break
                    time.sleep(0.5)
                
                # If still running, force kill
                if self.is_running():
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(1)
                
                # Clean up PID file
                if self.pid_file.exists():
                    self.pid_file.unlink()
                
                print(f"✓ Motion stopped (PID {pid})")
                return True, "Motion stopped successfully"
            else:
                return False, "Could not find Motion process ID"
                
        except ProcessLookupError:
            # Process already terminated
            if self.pid_file.exists():
                self.pid_file.unlink()
            return True, "Motion process already stopped"
        except Exception as e:
            return False, f"Error stopping Motion: {str(e)}"
    
    def restart(self):
        """
        Restart the Motion process
        
        Returns:
            tuple: (success: bool, message: str)
        """
        if self.is_running():
            success, msg = self.stop()
            if not success:
                return False, f"Failed to stop Motion: {msg}"
            time.sleep(1)
        
        return self.start()
    
    def get_status(self):
        """
        Get current status of Motion
        
        Returns:
            dict: Status information
        """
        status = {
            'running': self.is_running(),
            'motion_installed': self.is_motion_installed(),
            'config_ready': self.is_config_ready(),
            'pid': self.get_motion_pid() if self.is_running() else None,
            'log_file': str(self.log_file),
            'config_file': str(self.config_file)
        }
        return status


# Test the Motion Manager
if __name__ == "__main__":
    print("Testing Motion Manager...")
    manager = MotionManager()
    
    print("\nStatus:")
    status = manager.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    if not status['motion_installed']:
        print("\n⚠️  Motion is not installed. Please run build_motion.sh first.")
    elif not status['config_ready']:
        print("\n⚠️  Motion configuration not found. Please create config/motion.conf.")
    else:
        print("\n✓ Motion Manager is ready")

