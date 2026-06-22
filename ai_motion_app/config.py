"""
Configuration management for AI Motion Detection App
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .platform_utils import get_config_dir

class Config:
    """Manage application configuration and settings"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            self.config_dir = get_config_dir() / "zones"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "zone_config.json"
        
        # Default settings
        self.settings = {
            "camera_index": 0,  # 0 for Logitech C920
            "camera_width": 1280,
            "camera_height": 720,
            "camera_fps": 15,
            "video_source": "camera",  # "camera" or "video"
            "video_file_path": "",  # Path to video file when using video source
            "model_size": "yolo26n.pt",  # latest nano Ultralytics model for speed
            "model_imgsz": 640,
            "model_device": "auto",  # auto prefers MPS on Apple Silicon
            "confidence_threshold": 0.5,  # 50% confidence minimum
            "detection_interval_ms": 100,
            "alert_cooldown": 5,  # seconds between alerts
            "detection_classes": ["person"],  # Only detect people
            "zone_overlay_alpha": 0.3,  # Transparency of zone overlay
            "zone_color": (0, 255, 0),  # Green BGR
            "alert_zone_color": (0, 0, 255),  # Red BGR when person detected
            "bbox_color": (255, 0, 0),  # Blue BGR for bounding boxes
            "alert_min_overlap": 0.15,  # min bbox fraction overlapping zone
            "alert_activation_frames": 3,  # frames required before alert
            "show_debug": True,
        }
        
        self.zone_points: List[Tuple[int, int]] = []
        self.load()
    
    def load(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    self.settings.update(data.get('settings', {}))
                    self.zone_points = [tuple(p) for p in data.get('zone_points', [])]
                print(f"✓ Configuration loaded from {self.config_file}")
            except Exception as e:
                print(f"⚠ Error loading config: {e}")
    
    def save(self):
        """Save configuration to file"""
        try:
            data = {
                'settings': self.settings,
                'zone_points': self.zone_points
            }
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"⚠ Error saving config: {e}")
    
    def get(self, key: str, default=None) -> Any:
        """Get a configuration value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value"""
        self.settings[key] = value
        # Do not auto-save on every set to avoid IO churn; callers decide when to save
