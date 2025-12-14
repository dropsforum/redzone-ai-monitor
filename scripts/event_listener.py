"""
Event Listener for Motion Detection App
Monitors Motion events and triggers notifications
"""

import os
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime


class MotionEventHandler(FileSystemEventHandler):
    """Handle file system events from Motion captures"""
    
    def __init__(self, notification_handler, captures_dir):
        """
        Initialize event handler
        
        Args:
            notification_handler: NotificationHandler instance
            captures_dir (str): Directory where Motion saves captures
        """
        self.notification_handler = notification_handler
        self.captures_dir = Path(captures_dir)
        self.last_event_time = {}
        self.event_cooldown = 3  # seconds between events for same file
    
    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return
        
        # Only process image and video files
        if not any(event.src_path.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.mp4', '.avi']):
            return
        
        # Check cooldown
        now = time.time()
        if event.src_path in self.last_event_time:
            if now - self.last_event_time[event.src_path] < self.event_cooldown:
                return
        
        self.last_event_time[event.src_path] = now
        
        # Trigger notification
        file_name = os.path.basename(event.src_path)
        print(f"Motion detected! New capture: {file_name}")
        self.notification_handler.motion_detected(
            camera_name="Camera",
            image_path=event.src_path
        )
    
    def on_modified(self, event):
        """Handle file modification events"""
        # We mainly care about new files, but this can catch updates
        pass


class EventListener:
    """Listen for Motion detection events"""
    
    def __init__(self, captures_dir, notification_handler, event_file=None):
        """
        Initialize event listener
        
        Args:
            captures_dir (str): Directory where Motion saves captures
            notification_handler: NotificationHandler instance
            event_file (str): Optional path to event flag file
        """
        self.captures_dir = Path(captures_dir)
        self.notification_handler = notification_handler
        self.event_file = Path(event_file) if event_file else None
        self.observer = None
        self.running = False
        
        # Ensure captures directory exists
        self.captures_dir.mkdir(parents=True, exist_ok=True)
    
    def start(self):
        """Start listening for events"""
        if self.running:
            print("Event listener is already running")
            return
        
        print(f"Starting event listener for: {self.captures_dir}")
        
        # Set up file system observer
        event_handler = MotionEventHandler(
            self.notification_handler,
            self.captures_dir
        )
        
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.captures_dir), recursive=False)
        self.observer.start()
        self.running = True
        
        print("✓ Event listener started")
    
    def stop(self):
        """Stop listening for events"""
        if not self.running:
            return
        
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.observer = None
        
        self.running = False
        print("✓ Event listener stopped")
    
    def is_running(self):
        """Check if listener is running"""
        return self.running
    
    def wait(self):
        """Wait for events (blocking)"""
        if not self.running:
            raise RuntimeError("Event listener is not running")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping event listener...")
            self.stop()


# Alternative: Poll-based event listener for event file
class EventFileListener:
    """Listen for Motion events via event flag file"""
    
    def __init__(self, event_file, notification_handler):
        """
        Initialize event file listener
        
        Args:
            event_file (str): Path to event flag file
            notification_handler: NotificationHandler instance
        """
        self.event_file = Path(event_file)
        self.notification_handler = notification_handler
        self.running = False
        self.last_mtime = 0
    
    def start(self):
        """Start listening for event file changes"""
        if self.running:
            return
        
        self.running = True
        print(f"✓ Event file listener started: {self.event_file}")
        
        # Initialize last modified time
        if self.event_file.exists():
            self.last_mtime = self.event_file.stat().st_mtime
    
    def check_for_events(self):
        """Check if event file has been updated"""
        if not self.running:
            return False
        
        if not self.event_file.exists():
            return False
        
        try:
            current_mtime = self.event_file.stat().st_mtime
            
            if current_mtime > self.last_mtime:
                self.last_mtime = current_mtime
                
                # Read event data from file
                with open(self.event_file, 'r') as f:
                    event_data = f.read().strip()
                
                if event_data:
                    print(f"Motion event detected: {event_data}")
                    self.notification_handler.motion_detected()
                    return True
        except Exception as e:
            print(f"Error checking event file: {e}")
        
        return False
    
    def stop(self):
        """Stop listening"""
        self.running = False
        print("✓ Event file listener stopped")


# Test the event listener
if __name__ == "__main__":
    from notification_handler import NotificationHandler
    
    print("Testing Event Listener...")
    
    # Create test captures directory
    test_dir = Path("captures")
    test_dir.mkdir(exist_ok=True)
    
    # Initialize
    notif_handler = NotificationHandler()
    listener = EventListener(test_dir, notif_handler)
    
    print("\nStarting listener...")
    listener.start()
    
    print("\nListener is running. Create a test file in 'captures/' directory:")
    print("  touch captures/test_motion.jpg")
    print("\nPress Ctrl+C to stop...")
    
    try:
        listener.wait()
    except KeyboardInterrupt:
        print("\nStopping...")
        listener.stop()


