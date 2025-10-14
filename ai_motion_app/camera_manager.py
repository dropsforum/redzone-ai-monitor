"""
Camera Manager for AI Motion Detection App
Handles camera initialization and frame capture
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List

class CameraManager:
    """Manage camera capture and frame processing"""
    
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480, fps: int = 15):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_open = False
        self.available_cameras: List[int] = []
        
    def start(self) -> bool:
        """Initialize and start camera capture"""
        try:
            # Probe available cameras first for a better default
            if not self.available_cameras:
                self.enumerate_cameras()

            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                print(f"✗ Failed to open camera {self.camera_index}")
                # Try fallback to first available camera if present
                if self.available_cameras:
                    fallback = self.available_cameras[0]
                    if fallback != self.camera_index:
                        print(f"  Attempting fallback to camera {fallback}")
                        self.cap = cv2.VideoCapture(fallback)
                        if self.cap.isOpened():
                            self.camera_index = fallback
                        else:
                            return False
                else:
                    return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Verify settings
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            
            print(f"✓ Camera {self.camera_index} opened")
            print(f"  Resolution: {actual_width}x{actual_height}")
            print(f"  FPS: {actual_fps}")
            
            self.is_open = True
            return True
            
        except Exception as e:
            print(f"✗ Error starting camera: {e}")
            return False

    def enumerate_cameras(self, max_devices: int = 8) -> List[int]:
        """Detect available camera indices by probing."""
        indices: List[int] = []
        for idx in range(max_devices):
            cap = cv2.VideoCapture(idx)
            if cap is not None and cap.isOpened():
                indices.append(idx)
                cap.release()
        self.available_cameras = indices
        if not indices:
            print("⚠ No cameras detected")
        else:
            print(f"✓ Cameras available: {indices}")
        return indices

    def switch_camera(self, new_index: int) -> bool:
        """Switch to a different camera. Returns True if successful."""
        if new_index == self.camera_index:
            return True
        previous_cap = self.cap
        previous_index = self.camera_index
        try:
            # Try opening new camera first
            cap = cv2.VideoCapture(new_index)
            if not cap.isOpened():
                print(f"✗ Unable to open camera {new_index}")
                return False
            # Configure
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            cap.set(cv2.CAP_PROP_FPS, self.fps)
            # Swap over
            if previous_cap is not None:
                previous_cap.release()
            self.cap = cap
            self.camera_index = new_index
            self.is_open = True
            print(f"✓ Switched to camera {new_index}")
            return True
        except Exception as e:
            print(f"✗ Error switching camera: {e}")
            # Restore previous state if needed
            self.cap = previous_cap
            self.camera_index = previous_index
            self.is_open = previous_cap is not None
            return False
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from the camera
        Returns: (success, frame)
        """
        if not self.is_open or self.cap is None:
            return False, None
        
        ret, frame = self.cap.read()
        return ret, frame
    
    def stop(self):
        """Stop camera capture and release resources"""
        if self.cap is not None:
            self.cap.release()
            self.is_open = False
            print("✓ Camera released")
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.stop()


