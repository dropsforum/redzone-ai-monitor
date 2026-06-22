"""
Camera Manager for AI Motion Detection App
Handles camera initialization and frame capture
"""

import cv2
import numpy as np
import time
from pathlib import Path
from typing import Optional, Tuple, List

class CameraManager:
    """Manage camera capture and frame processing"""
    
    def __init__(
        self,
        camera_index: int = 0,
        width: int = 1280,
        height: int = 720,
        fps: int = 15,
        source_type: str = "camera",
        video_path: Optional[str] = None,
    ):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_open = False
        self.available_cameras: List[int] = []
        self.source_type = source_type if source_type in ("camera", "video") else "camera"
        self.video_path = Path(video_path).expanduser() if video_path else None
        self.total_frames: int = 0
        self.current_frame_number: int = 0
        self.current_frame: Optional[np.ndarray] = None
        self.playback_active = False
        self.playback_started_at = 0.0
        self.playback_started_frame = 0
        
    def start(self) -> bool:
        """Initialize and start camera capture"""
        try:
            # Reset counters and close existing capture if any
            if self.cap is not None:
                self.cap.release()
            self.cap = None
            self.is_open = False
            self.current_frame_number = 0
            self.total_frames = 0

            if self.source_type == "video":
                if self.video_path is None:
                    print("✗ Video source selected but no file path provided")
                    return False
                if not self.video_path.exists():
                    print(f"✗ Video file not found: {self.video_path}")
                    return False

                self.cap = cv2.VideoCapture(str(self.video_path))
                if not self.cap.isOpened():
                    print(f"✗ Failed to open video file: {self.video_path}")
                    return False

                self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
                actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                actual_fps = float(self.cap.get(cv2.CAP_PROP_FPS) or 0.0)

                if actual_width > 0:
                    self.width = actual_width
                if actual_height > 0:
                    self.height = actual_height
                if actual_fps > 0:
                    self.fps = actual_fps

                print(f"✓ Video source opened: {self.video_path}")
                print(f"  Resolution: {self.width}x{self.height}")
                if self.total_frames > 0:
                    print(f"  Frames: {self.total_frames}")
                print(f"  FPS: {self.fps:.2f}")

                self.is_open = True
                self.playback_active = False
                self.current_frame = None
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.current_frame = frame
                    self.current_frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.current_frame_number = 0
                return True

            self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                print(f"✗ Failed to open camera {self.camera_index}")
                # Try fallback to first available camera if present
                if not self.available_cameras:
                    self.enumerate_cameras()
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

    def frame_delay_ms(self) -> int:
        """Return a display wait time that preserves recorded-video playback speed."""
        if self.source_type == "video" and self.fps > 0:
            return max(1, int(round(1000.0 / float(self.fps))))
        return 1

    def start_playback(self, restart: bool = False):
        """Start or resume recorded-video playback using wall-clock timing."""
        if self.source_type != "video" or self.cap is None:
            return
        if restart:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.current_frame_number = 0
        self.playback_active = True
        self.playback_started_at = time.monotonic()
        self.playback_started_frame = self.current_frame_number

    def pause_playback(self):
        """Pause recorded-video playback without releasing the file."""
        if self.source_type == "video":
            self.playback_active = False

    def _sync_video_position(self):
        """Skip frames when display work falls behind so videos keep real speed."""
        if self.source_type != "video" or self.cap is None or not self.playback_active or self.fps <= 0:
            return
        elapsed = time.monotonic() - self.playback_started_at
        target_frame = self.playback_started_frame + int(elapsed * float(self.fps))
        if self.total_frames > 0:
            target_frame = target_frame % self.total_frames
        if target_frame > self.current_frame_number + 1:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
            self.current_frame_number = target_frame

    def enumerate_cameras(self, max_devices: int = 8) -> List[int]:
        """Detect available camera indices by probing."""
        indices: List[int] = []
        if self.source_type != "camera":
            # Camera enumeration is irrelevant for video files
            self.available_cameras = indices
            return indices
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
        if self.source_type != "camera":
            print("⚠ Camera switching is disabled when using a video file source.")
            return False
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
        
        if self.source_type == "video" and not self.playback_active:
            if self.current_frame is not None:
                return True, self.current_frame.copy()
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.current_frame = frame
                return True, frame.copy()
            return False, None

        self._sync_video_position()
        ret, frame = self.cap.read()
        if self.source_type == "video":
            if not ret or frame is None:
                # Loop back to start
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.current_frame_number = 0
                self.start_playback(restart=False)
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    return False, None
            self.current_frame_number = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.current_frame = frame
        else:
            self.current_frame_number = 0
        return ret, frame
    
    def stop(self):
        """Stop camera capture and release resources"""
        if self.cap is not None:
            self.cap.release()
            self.is_open = False
            self.playback_active = False
            print("✓ Camera released")
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.stop()
