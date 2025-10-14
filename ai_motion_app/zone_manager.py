"""
Zone Manager for AI Motion Detection App
Handles polygon zone definition and intersection detection
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional

class ZoneManager:
    """Manage detection zones and check for object intersection"""
    
    def __init__(self):
        self.points: List[Tuple[int, int]] = []
        self.is_closed = False
        self.temp_point: Optional[Tuple[int, int]] = None  # For drawing line to cursor
        
    def add_point(self, x: int, y: int):
        """Add a point to the polygon"""
        if not self.is_closed:
            self.points.append((x, y))
            print(f"  Point added: ({x}, {y}) - Total points: {len(self.points)}")
    
    def close_polygon(self):
        """Close the polygon (must have at least 3 points)"""
        if len(self.points) >= 3:
            self.is_closed = True
            print(f"✓ Zone closed with {len(self.points)} points")
            return True
        else:
            print(f"✗ Need at least 3 points to close zone (have {len(self.points)})")
            return False
    
    def clear(self):
        """Clear the current zone"""
        self.points = []
        self.is_closed = False
        self.temp_point = None
        print("✓ Zone cleared")
    
    def set_temp_point(self, x: int, y: int):
        """Set temporary point for drawing line to cursor"""
        if not self.is_closed and len(self.points) > 0:
            self.temp_point = (x, y)
    
    def draw_zone(self, frame: np.ndarray, color: Tuple[int, int, int] = (0, 255, 0), 
                  alpha: float = 0.3, thickness: int = 2):
        """
        Draw the zone on the frame
        Args:
            frame: The image to draw on
            color: BGR color tuple
            alpha: Transparency (0-1)
            thickness: Line thickness
        """
        if len(self.points) == 0:
            return frame
        
        overlay = frame.copy()
        
        # Draw lines between points
        for i in range(len(self.points)):
            start = self.points[i]
            end = self.points[(i + 1) % len(self.points)] if self.is_closed else \
                  (self.points[i + 1] if i < len(self.points) - 1 else None)
            
            if end is not None:
                cv2.line(overlay, start, end, color, thickness)
        
        # Draw line to cursor if in drawing mode
        if not self.is_closed and self.temp_point is not None and len(self.points) > 0:
            cv2.line(overlay, self.points[-1], self.temp_point, color, 1)
        
        # Draw filled polygon if closed
        if self.is_closed and len(self.points) >= 3:
            pts = np.array(self.points, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.fillPoly(overlay, [pts], color)
        
        # Draw points
        for point in self.points:
            cv2.circle(overlay, point, 5, color, -1)
            cv2.circle(overlay, point, 6, (255, 255, 255), 1)
        
        # Blend overlay with original frame
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        return frame
    
    def point_in_polygon(self, x: int, y: int) -> bool:
        """
        Check if a point is inside the polygon using ray casting algorithm
        Args:
            x, y: Point coordinates
        Returns:
            True if point is inside polygon
        """
        if not self.is_closed or len(self.points) < 3:
            return False
        
        n = len(self.points)
        inside = False
        
        p1x, p1y = self.points[0]
        for i in range(1, n + 1):
            p2x, p2y = self.points[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def bbox_zone_overlap_ratio(self, bbox: Tuple[int, int, int, int], frame_shape: Tuple[int, int]) -> float:
        """Return fraction of bbox area that overlaps the zone (0..1).
        Uses binary masks (fast enough at 640x480).
        """
        if not self.is_closed or len(self.points) < 3:
            return 0.0
        h, w = frame_shape
        x1, y1, x2, y2 = bbox
        x1 = max(0, min(w - 1, x1))
        x2 = max(0, min(w - 1, x2))
        y1 = max(0, min(h - 1, y1))
        y2 = max(0, min(h - 1, y2))
        if x2 <= x1 or y2 <= y1:
            return 0.0
        # Zone mask
        zone_mask = np.zeros((h, w), dtype=np.uint8)
        pts = np.array(self.points, np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(zone_mask, [pts], 255)
        # BBox mask
        rect_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.rectangle(rect_mask, (x1, y1), (x2, y2), 255, -1)
        # Overlap
        overlap = cv2.bitwise_and(zone_mask, rect_mask)
        overlap_area = int(cv2.countNonZero(overlap))
        bbox_area = int((x2 - x1) * (y2 - y1))
        if bbox_area <= 0:
            return 0.0
        return float(overlap_area) / float(bbox_area)

    def bbox_intersects_zone(self, bbox: Tuple[int, int, int, int], frame_shape: Tuple[int, int], threshold: float = 0.1) -> bool:
        """Boolean convenience wrapper using overlap ratio with threshold."""
        return self.bbox_zone_overlap_ratio(bbox, frame_shape) >= threshold
    
    def has_zone(self) -> bool:
        """Check if a valid zone is defined"""
        return self.is_closed and len(self.points) >= 3
    
    def get_points(self) -> List[Tuple[int, int]]:
        """Get the current polygon points"""
        return self.points.copy()
    
    def set_points(self, points: List[Tuple[int, int]]):
        """Set polygon points from saved configuration"""
        self.points = points.copy()
        if len(self.points) >= 3:
            self.is_closed = True
            print(f"✓ Zone loaded with {len(self.points)} points")


