"""
Motion Detection Mac App
Menu bar application for controlling Motion detection
"""

import rumps
import webbrowser
from pathlib import Path
from motion_manager import MotionManager
from notification_handler import NotificationHandler
from event_listener import EventListener


class MotionApp(rumps.App):
    """Menu bar application for Motion detection"""
    
    def __init__(self):
        super(MotionApp, self).__init__(
            "Motion Detector",
            icon=None,
            quit_button=None
        )
        
        # Initialize components
        self.project_root = Path(__file__).parent
        self.motion_manager = MotionManager(self.project_root)
        self.notification_handler = NotificationHandler()
        self.event_listener = EventListener(
            self.project_root / "captures",
            self.notification_handler
        )
        
        # Menu items
        self.menu = [
            rumps.MenuItem("Start Monitoring", callback=self.start_monitoring),
            rumps.MenuItem("Stop Monitoring", callback=self.stop_monitoring),
            rumps.separator,
            rumps.MenuItem("View Camera Feed", callback=self.view_feed),
            rumps.MenuItem("Open Captures Folder", callback=self.open_captures),
            rumps.separator,
            rumps.MenuItem("Status", callback=self.show_status),
            rumps.separator,
            rumps.MenuItem("Quit", callback=self.quit_app)
        ]
        
        # Update initial state
        self.update_menu_state()
        self.update_title()
    
    def update_title(self):
        """Update menu bar title based on monitoring state"""
        if self.motion_manager.is_running():
            self.title = "👁️"  # Eye emoji when monitoring
        else:
            self.title = "💤"  # Sleeping emoji when idle
    
    def update_menu_state(self):
        """Enable/disable menu items based on current state"""
        is_running = self.motion_manager.is_running()
        
        # Enable/disable menu items
        self.menu["Start Monitoring"].set_callback(self.start_monitoring if not is_running else None)
        self.menu["Stop Monitoring"].set_callback(self.stop_monitoring if is_running else None)
    
    @rumps.clicked("Start Monitoring")
    def start_monitoring(self, _):
        """Start motion detection"""
        # Check prerequisites
        if not self.motion_manager.is_motion_installed():
            rumps.alert(
                "Motion Not Installed",
                "Please run build_motion.sh to install Motion first.",
                ok="OK"
            )
            return
        
        if not self.motion_manager.is_config_ready():
            rumps.alert(
                "Configuration Missing",
                "Please create config/motion.conf before starting.\n\nRun: python3 create_config.py",
                ok="OK"
            )
            return
        
        # Start Motion
        success, message = self.motion_manager.start()
        
        if success:
            # Start event listener
            self.event_listener.start()
            
            # Send notification
            self.notification_handler.app_started()
            
            # Update UI
            self.update_title()
            self.update_menu_state()
            
            rumps.notification(
                title="Motion Detector",
                subtitle="Monitoring Started",
                message="Camera monitoring is now active"
            )
        else:
            rumps.alert(
                "Failed to Start",
                message,
                ok="OK"
            )
    
    @rumps.clicked("Stop Monitoring")
    def stop_monitoring(self, _):
        """Stop motion detection"""
        success, message = self.motion_manager.stop()
        
        if success or not self.motion_manager.is_running():
            # Stop event listener
            self.event_listener.stop()
            
            # Send notification
            self.notification_handler.app_stopped()
            
            # Update UI
            self.update_title()
            self.update_menu_state()
            
            rumps.notification(
                title="Motion Detector",
                subtitle="Monitoring Stopped",
                message="Camera monitoring has been disabled"
            )
        else:
            rumps.alert(
                "Failed to Stop",
                message,
                ok="OK"
            )
    
    @rumps.clicked("View Camera Feed")
    def view_feed(self, _):
        """Open camera feed in web browser"""
        if not self.motion_manager.is_running():
            rumps.alert(
                "Not Running",
                "Start monitoring first to view the camera feed.",
                ok="OK"
            )
            return
        
        # Open web interface (default Motion port is 8080)
        webbrowser.open("http://localhost:8080")
    
    @rumps.clicked("Open Captures Folder")
    def open_captures(self, _):
        """Open folder containing captured images/videos"""
        captures_dir = self.project_root / "captures"
        
        # Create directory if it doesn't exist
        captures_dir.mkdir(exist_ok=True)
        
        # Open in Finder
        import subprocess
        subprocess.run(["open", str(captures_dir)])
    
    @rumps.clicked("Status")
    def show_status(self, _):
        """Show current status"""
        status = self.motion_manager.get_status()
        
        status_text = []
        status_text.append(f"Running: {'✓ Yes' if status['running'] else '✗ No'}")
        status_text.append(f"Motion Installed: {'✓ Yes' if status['motion_installed'] else '✗ No'}")
        status_text.append(f"Config Ready: {'✓ Yes' if status['config_ready'] else '✗ No'}")
        
        if status['pid']:
            status_text.append(f"Process ID: {status['pid']}")
        
        status_text.append(f"\nConfig: {status['config_file']}")
        status_text.append(f"Log: {status['log_file']}")
        
        rumps.alert(
            "Motion Detector Status",
            "\n".join(status_text),
            ok="OK"
        )
    
    def quit_app(self, _):
        """Quit the application"""
        # Stop monitoring if running
        if self.motion_manager.is_running():
            print("Stopping monitoring before quit...")
            self.motion_manager.stop()
            self.event_listener.stop()
        
        rumps.quit_application()


def main():
    """Run the application"""
    print("Starting Motion Detection App...")
    print("Look for the app icon in your menu bar")
    
    app = MotionApp()
    app.run()


if __name__ == "__main__":
    main()


