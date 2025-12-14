"""
Alert System for AI Motion Detection App
Handles audible alerts and notifications
"""

import time
from datetime import datetime
from typing import Optional

from .platform_utils import play_default_alert

class AlertSystem:
    """Manage alerts and notifications when person detected in zone"""
    
    def __init__(self, cooldown_seconds: int = 5):
        """
        Initialize alert system
        Args:
            cooldown_seconds: Minimum seconds between alerts
        """
        self.cooldown_seconds = cooldown_seconds
        self.last_alert_time: float = 0
        self.alert_count: int = 0
        self.last_alert_timestamp: Optional[str] = None
        
    def can_alert(self) -> bool:
        """Check if enough time has passed since last alert"""
        current_time = time.time()
        return (current_time - self.last_alert_time) >= self.cooldown_seconds
    
    def trigger_alert(self):
        """Trigger an audible alert if cooldown has passed"""
        if not self.can_alert():
            return False
        
        try:
            # Play platform-appropriate alert sound
            play_default_alert()
            
            self.last_alert_time = time.time()
            self.alert_count += 1
            self.last_alert_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"🔔 ALERT #{self.alert_count}: Person detected in zone!")
            print(f"   Time: {self.last_alert_timestamp}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error triggering alert: {e}")
            return False
    
    def get_status(self) -> dict:
        """Get current alert system status"""
        return {
            'total_alerts': self.alert_count,
            'last_alert': self.last_alert_timestamp,
            'cooldown_seconds': self.cooldown_seconds,
            'can_alert_now': self.can_alert()
        }
    
    def get_cooldown_remaining(self) -> float:
        """Get seconds remaining until next alert can trigger"""
        if self.can_alert():
            return 0
        
        elapsed = time.time() - self.last_alert_time
        remaining = self.cooldown_seconds - elapsed
        return max(0, remaining)
    
    def reset_stats(self):
        """Reset alert statistics"""
        self.alert_count = 0
        self.last_alert_timestamp = None
        print("✓ Alert statistics reset")



