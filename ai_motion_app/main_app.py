"""
Main Application for AI Motion Detection
OpenCV-based interface for zone drawing and monitoring
"""

import cv2
import time
import numpy as np
from typing import Optional

from .camera_manager import CameraManager
from .ai_detector import AIDetector
from .zone_manager import ZoneManager
from .alert_system import AlertSystem
from .config import Config


class MotionDetectionApp:
    """Main application class"""
    
    # Application states
    STATE_SETUP = "setup"
    STATE_DRAWING = "drawing"
    STATE_MONITORING = "monitoring"
    STATE_PAUSED = "paused"
    
    def __init__(self):
        # Load configuration
        self.config = Config()
        
        # Initialize components
        self.camera = CameraManager(
            camera_index=self.config.get('camera_index', 0),
            width=self.config.get('camera_width', 1280),
            height=self.config.get('camera_height', 720),
            fps=self.config.get('camera_fps', 15),
            source_type=self.config.get('video_source', 'camera'),
            video_path=self.config.get('video_file_path', '')
        )
        
        self.detector = AIDetector(
            model_name=self.config.get('model_size', 'yolov8n.pt'),
            confidence_threshold=self.config.get('confidence_threshold', 0.5)
        )
        
        self.zone = ZoneManager()
        self.alert = AlertSystem(
            cooldown_seconds=self.config.get('alert_cooldown', 5)
        )
        
        # Application state
        self.state = self.STATE_SETUP
        self.running = False
        self.window_name = "DROPS Red Zone Monitoring"
        
        # Performance metrics
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        self.alert_frames = 0  # consecutive frames that meet alert criteria
        
        # Traffic light state: 'green', 'yellow', 'red'
        self.traffic_light = 'green'
        
        # Mouse position for drawing
        self.mouse_x = 0
        self.mouse_y = 0
        
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for zone drawing"""
        # Account for top border offset (60 pixels)
        TOP_BORDER = 60
        
        # Adjust y coordinate to video frame coordinates
        video_y = y - TOP_BORDER
        
        # Only process if click is within video area
        if video_y < 0:
            return
            
        self.mouse_x = x
        self.mouse_y = video_y
        
        if self.state == self.STATE_DRAWING:
            self.zone.set_temp_point(x, video_y)
            
            if event == cv2.EVENT_LBUTTONDOWN:
                # Add point on left click (using video coordinates)
                self.zone.add_point(x, video_y)
                
    def draw_ui(self, frame: np.ndarray) -> np.ndarray:
        """Draw UI elements in border areas without overlaying video"""
        height, width = frame.shape[:2]
        
        # Calculate FPS
        self.frame_count += 1
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            self.fps = self.frame_count / elapsed
        
        # Create expanded canvas with borders for UI
        top_border = 60
        bottom_border = 150
        new_height = height + top_border + bottom_border
        
        # Create black canvas
        canvas = np.zeros((new_height, width, 3), dtype=np.uint8)
        
        # Place original frame in the middle (preserving video without overlay)
        canvas[top_border:top_border + height, 0:width] = frame
        
        # === TOP STATUS BAR (no overlay on video) ===
        # Status indicator
        state_colors = {
            self.STATE_SETUP: (100, 100, 100),
            self.STATE_DRAWING: (0, 165, 255),
            self.STATE_MONITORING: (0, 255, 0),
            self.STATE_PAUSED: (0, 165, 255)
        }
        
        state_text = {
            self.STATE_SETUP: "SETUP MODE",
            self.STATE_DRAWING: "DRAWING ZONE",
            self.STATE_MONITORING: "Red Zone Monitoring Active",
            self.STATE_PAUSED: "PAUSED"
        }
        
        color = state_colors.get(self.state, (255, 255, 255))
        text = state_text.get(self.state, "UNKNOWN")
        
        cv2.putText(canvas, text, (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # FPS, Camera, Zone, and Alert info on same line
        if self.camera.source_type == "video":
            video_label = "Video: "
            if self.camera.video_path:
                video_label += self.camera.video_path.name
            else:
                video_label += "Unknown"
            if self.camera.total_frames > 0:
                current = min(self.camera.current_frame_number, self.camera.total_frames)
                video_label += f" (Frame {current}/{self.camera.total_frames})"
            info_text = f"FPS: {self.fps:.1f}  {video_label}"
        else:
            info_text = f"FPS: {self.fps:.1f}  Cam: {self.camera.camera_index}"
        cv2.putText(canvas, info_text, (10, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        zone_text = f"Zone: {'Defined' if self.zone.has_zone() else 'Not Set'}"
        zone_color = (0, 255, 0) if self.zone.has_zone() else (0, 0, 255)
        cv2.putText(canvas, zone_text, (150, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, zone_color, 1)
        
        # Alert status
        if self.state == self.STATE_MONITORING:
            status = self.alert.get_status()
            alert_text = f"Alerts: {status['total_alerts']}"
            if status['last_alert']:
                alert_text += f" | Last: {status['last_alert']}"
            cv2.putText(canvas, alert_text, (320, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        # === BOTTOM CONTROLS BAR (no overlay on video) ===
        shortcuts_y = top_border + height + 15
        
        # Draw separator line
        cv2.line(canvas, (0, top_border + height), (width, top_border + height), 
                (50, 50, 50), 2)
        
        shortcuts = [
            "D: Draw Zone",
            "ENTER: Close Zone",
            "C: Clear Zone",
            "M: Switch Camera",
            "S: Start Monitoring",
            "P: Pause",
            "Q: Quit"
        ]
        
        y_pos = shortcuts_y
        for shortcut in shortcuts:
            cv2.putText(canvas, shortcut, (10, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            y_pos += 22
        
        # === TRAFFIC LIGHT (bottom right) ===
        if self.state == self.STATE_MONITORING:
            light_x = width - 80
            light_y = top_border + height + 30
            light_radius = 20
            light_spacing = 50
            
            # Define colors for each light (BGR format)
            # Active lights are bright, inactive are dimmed
            lights = {
                'red': (0, 0, 255) if self.traffic_light == 'red' else (0, 0, 80),
                'yellow': (0, 255, 255) if self.traffic_light == 'yellow' else (0, 80, 80),
                'green': (0, 255, 0) if self.traffic_light == 'green' else (0, 80, 0)
            }
            
            # Draw red light (top)
            cv2.circle(canvas, (light_x, light_y), light_radius, lights['red'], -1)
            cv2.circle(canvas, (light_x, light_y), light_radius, (100, 100, 100), 2)
            
            # Draw yellow light (middle)
            cv2.circle(canvas, (light_x, light_y + light_spacing), light_radius, lights['yellow'], -1)
            cv2.circle(canvas, (light_x, light_y + light_spacing), light_radius, (100, 100, 100), 2)
            
            # Draw green light (bottom)
            cv2.circle(canvas, (light_x, light_y + light_spacing * 2), light_radius, lights['green'], -1)
            cv2.circle(canvas, (light_x, light_y + light_spacing * 2), light_radius, (100, 100, 100), 2)
        
        return canvas
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """Process a single frame"""
        # Draw zone if defined
        if self.zone.has_zone() or len(self.zone.points) > 0:
            zone_color = self.config.get('zone_color', (0, 255, 0))
            
            # Change color if person detected in zone during monitoring
            if self.state == self.STATE_MONITORING:
                zone_color = self.config.get('zone_color', (0, 255, 0))
            
            frame = self.zone.draw_zone(
                frame, 
                color=zone_color,
                alpha=self.config.get('zone_overlay_alpha', 0.3)
            )
        
        # Run detection if monitoring
        if self.state == self.STATE_MONITORING and self.zone.has_zone():
            detections = self.detector.detect_people(frame)

            # Evaluate overlap-based alert condition
            min_overlap = float(self.config.get('alert_min_overlap', 0.15))
            activation_frames = int(self.config.get('alert_activation_frames', 3))
            bbox_color = self.config.get('bbox_color', (255, 0, 0))

            hit_this_frame = False
            max_overlap = 0.0  # Track maximum overlap for traffic light
            
            for x1, y1, x2, y2, conf in detections:
                overlap = self.zone.bbox_zone_overlap_ratio((x1, y1, x2, y2), frame.shape[:2])
                max_overlap = max(max_overlap, overlap)
                
                if overlap >= min_overlap:
                    hit_this_frame = True
                    # Draw detection with alert color and overlap
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 3)
                    label = f"ALERT {conf:.2f} ovl {overlap:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                else:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), bbox_color, 2)
                    label = f"Person {conf:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            # Update traffic light state based on max overlap
            if max_overlap >= min_overlap:
                self.traffic_light = 'red'
            elif max_overlap > 0:
                self.traffic_light = 'yellow'
            else:
                self.traffic_light = 'green'

            # Debounce: require N consecutive frames
            self.alert_frames = self.alert_frames + 1 if hit_this_frame else 0
            if self.alert_frames >= activation_frames:
                self.alert.trigger_alert()
                frame = self.zone.draw_zone(frame, color=self.config.get('alert_zone_color', (0, 0, 255)), alpha=0.4)
                # keep alert_frames saturated to avoid overflow
                self.alert_frames = activation_frames
        else:
            # Reset traffic light when not monitoring
            self.traffic_light = 'green'
        
        # Draw UI
        frame = self.draw_ui(frame)
        
        return frame
    
    def handle_key(self, key: int):
        """Handle keyboard input"""
        if key == ord('q') or key == ord('Q') or key == 27:  # Q or ESC
            self.running = False
            print("\n👋 Quitting application...")
            
        elif key == ord('d') or key == ord('D'):
            if self.state != self.STATE_DRAWING:
                self.state = self.STATE_DRAWING
                print("\n✏️  Entering zone drawing mode")
                print("  • Click to add points")
                print("  • Press ENTER to close zone")
                print("  • Press ESC to cancel")
            
        elif key == ord('c') or key == ord('C'):
            self.zone.clear()
            if self.state == self.STATE_MONITORING:
                self.state = self.STATE_SETUP
            print("\n🗑️  Zone cleared")
            
        elif key == 13:  # ENTER
            if self.state == self.STATE_DRAWING:
                if self.zone.close_polygon():
                    self.state = self.STATE_SETUP
                    print("  Zone ready for monitoring!")
                    
        elif key == ord('s') or key == ord('S'):
            if self.zone.has_zone():
                self.state = self.STATE_MONITORING
                print("\n👁️  Monitoring started!")
            else:
                print("\n⚠️  Please define a zone first (press D)")
                
        elif key == ord('p') or key == ord('P'):
            if self.state == self.STATE_MONITORING:
                self.state = self.STATE_PAUSED
                print("\n⏸️  Monitoring paused")
            elif self.state == self.STATE_PAUSED:
                self.state = self.STATE_MONITORING
                print("\n▶️  Monitoring resumed")
        
        elif key == ord('m') or key == ord('M'):
            # Cycle through available cameras
            if self.camera.source_type != "camera":
                print("\n⚠️ Camera switching is disabled while using a video file source.")
                return
            if not self.camera.available_cameras:
                self.camera.enumerate_cameras()
            cams = self.camera.available_cameras or [self.camera.camera_index]
            if cams:
                try:
                    idx = cams.index(self.camera.camera_index)
                except ValueError:
                    idx = 0
                next_idx = cams[(idx + 1) % len(cams)]
                if self.camera.switch_camera(next_idx):
                    # Persist selection
                    self.config.set('camera_index', next_idx)
                    self.config.save()
                    print(f"\n📷 Switched to camera {next_idx}")
                else:
                    print(f"\n⚠️ Could not switch to camera {next_idx}")
    
    def run(self):
        """Main application loop"""
        print("\n" + "="*60)
        print("DROPS Red Zone Monitoring")
        print("="*60)
        
        # Start camera
        if not self.camera.start():
            if self.camera.source_type == "video":
                print("✗ Failed to start video source. Please verify 'video_file_path' in the configuration.")
            else:
                print("✗ Failed to start camera. Exiting.")
            return

        # Create window and set mouse callback early
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)

        # Loading indicator while model initializes
        print("\nLoading AI model… this can take up to ~2 minutes on first run.")
        loading_img = np.zeros((self.camera.height + 210, self.camera.width, 3), dtype=np.uint8)
        t0 = time.time()
        shown_once = False
        while not shown_once:
            msg = "Loading AI model…"
            cv2.putText(loading_img, msg, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
            cv2.imshow(self.window_name, loading_img)
            cv2.waitKey(100)
            shown_once = True

        # Load AI model
        if not self.detector.load_model():
            print("✗ Failed to load AI model. Exiting.")
            self.camera.stop()
            return
        print(f"✓ AI model loaded in {time.time() - t0:.1f}s")

        # Load saved zone if exists
        if len(self.config.zone_points) > 0:
            self.zone.set_points(self.config.zone_points)
            print(f"✓ Loaded saved zone with {len(self.config.zone_points)} points")
        
        print("\n✓ Application ready!")
        print("\nPress 'D' to draw a detection zone")
        print("="*60 + "\n")
        
        self.running = True
        
        try:
            while self.running:
                # Read frame
                ret, frame = self.camera.read_frame()
                if not ret:
                    print("✗ Failed to read frame from camera")
                    break
                
                # Process frame
                frame = self.process_frame(frame)
                
                # Display frame
                cv2.imshow(self.window_name, frame)
                
                # Handle keyboard input (1ms wait)
                key = cv2.waitKey(1) & 0xFF
                if key != 255:  # Key was pressed
                    self.handle_key(key)
                    
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            
        finally:
            # Cleanup
            print("\nCleaning up...")
            
            # Save zone configuration
            if self.zone.has_zone():
                self.config.zone_points = self.zone.get_points()
                self.config.save()
            
            self.camera.stop()
            cv2.destroyAllWindows()
            
            # Print statistics
            stats = self.alert.get_status()
            print("\n" + "="*60)
            print("Session Summary:")
            print(f"  Total runtime: {time.time() - self.start_time:.1f}s")
            print(f"  Average FPS: {self.fps:.1f}")
            print(f"  Total alerts: {stats['total_alerts']}")
            if stats['last_alert']:
                print(f"  Last alert: {stats['last_alert']}")
            print("="*60)
            print("\n✓ Application closed\n")

