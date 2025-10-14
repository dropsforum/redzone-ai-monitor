"""
Notification Handler for Motion Detection App
Sends macOS notifications when motion is detected
"""

import subprocess
import os
from datetime import datetime


class NotificationHandler:
    """Handle macOS notifications for motion detection events"""
    
    def __init__(self):
        self.app_name = "Motion Detector"
        self.last_notification_time = None
        self.notification_cooldown = 5  # seconds between notifications
    
    def send_notification(self, title, message, sound=True):
        """
        Send a native macOS notification
        
        Args:
            title (str): Notification title
            message (str): Notification message
            sound (bool): Whether to play a sound
        """
        try:
            # Check cooldown to prevent notification spam
            now = datetime.now()
            if self.last_notification_time:
                time_diff = (now - self.last_notification_time).total_seconds()
                if time_diff < self.notification_cooldown:
                    print(f"Notification cooldown active ({time_diff:.1f}s elapsed)")
                    return
            
            # Build AppleScript command for notification
            sound_str = " sound name \"Hero\"" if sound else ""
            script = f'''
            display notification "{message}" with title "{self.app_name}" subtitle "{title}"{sound_str}
            '''
            
            # Execute AppleScript
            subprocess.run(
                ['osascript', '-e', script],
                check=True,
                capture_output=True
            )
            
            self.last_notification_time = now
            print(f"✓ Notification sent: {title} - {message}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error sending notification: {e}")
        except Exception as e:
            print(f"Unexpected error sending notification: {e}")
    
    def motion_detected(self, camera_name="Camera", image_path=None):
        """
        Send notification for motion detection event
        
        Args:
            camera_name (str): Name of the camera that detected motion
            image_path (str): Path to captured image (optional)
        """
        title = "Motion Detected!"
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"{camera_name} at {timestamp}"
        
        if image_path and os.path.exists(image_path):
            message += f"\nImage saved: {os.path.basename(image_path)}"
        
        self.send_notification(title, message, sound=True)
    
    def app_started(self):
        """Send notification when monitoring starts"""
        self.send_notification(
            "Monitoring Started",
            "Motion detection is now active",
            sound=False
        )
    
    def app_stopped(self):
        """Send notification when monitoring stops"""
        self.send_notification(
            "Monitoring Stopped",
            "Motion detection has been disabled",
            sound=False
        )
    
    def error_notification(self, error_message):
        """Send notification for errors"""
        self.send_notification(
            "Error",
            error_message,
            sound=True
        )


# Test the notification system
if __name__ == "__main__":
    print("Testing notification system...")
    handler = NotificationHandler()
    
    print("\n1. Testing basic notification...")
    handler.send_notification("Test", "This is a test notification")
    
    print("\n2. Testing motion detection notification...")
    handler.motion_detected("Logitech Camera")
    
    print("\n3. Testing app started notification...")
    handler.app_started()
    
    print("\nNotification tests complete!")


