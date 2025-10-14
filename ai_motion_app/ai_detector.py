"""
AI Detection Engine for Motion Detection App
Uses YOLOv8 for object detection
"""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple, Optional
import os

class AIDetector:
    """AI-powered object detection using YOLOv8"""
    
    # COCO dataset class names (YOLO is trained on COCO)
    # Person class is index 0
    PERSON_CLASS_ID = 0
    
    def __init__(self, model_name: str = "yolov8n.pt", confidence_threshold: float = 0.5):
        """
        Initialize the AI detector
        Args:
            model_name: YOLO model size (n=nano, s=small, m=medium, l=large)
            confidence_threshold: Minimum confidence for detections (0-1)
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.model: Optional[YOLO] = None
        self.is_loaded = False
        
    def load_model(self) -> bool:
        """Load the YOLO model"""
        try:
            print(f"Loading YOLO model: {self.model_name}...")
            self.model = YOLO(self.model_name)
            self.is_loaded = True
            print(f"✓ YOLO model loaded successfully")
            return True
        except Exception as e:
            print(f"✗ Error loading YOLO model: {e}")
            return False
    
    def detect_people(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Detect people in the frame
        Args:
            frame: Input image (BGR format from OpenCV)
        Returns:
            List of detections: [(x1, y1, x2, y2, confidence), ...]
        """
        if not self.is_loaded or self.model is None:
            return []
        
        try:
            # Run inference
            results = self.model(frame, verbose=False, conf=self.confidence_threshold)
            
            detections = []
            
            # Process results
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    # Get class ID
                    class_id = int(box.cls[0])
                    
                    # Only process person detections (class 0)
                    if class_id == self.PERSON_CLASS_ID:
                        # Get bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0])
                        
                        detections.append((
                            int(x1), int(y1), int(x2), int(y2), confidence
                        ))
            
            return detections
            
        except Exception as e:
            print(f"✗ Error during detection: {e}")
            return []
    
    def draw_detections(self, frame: np.ndarray, detections: List[Tuple[int, int, int, int, float]],
                       color: Tuple[int, int, int] = (255, 0, 0), thickness: int = 2) -> np.ndarray:
        """
        Draw bounding boxes around detected people
        Args:
            frame: Input image
            detections: List of (x1, y1, x2, y2, confidence)
            color: BGR color for bounding boxes
            thickness: Line thickness
        Returns:
            Frame with drawn detections
        """
        for x1, y1, x2, y2, conf in detections:
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # Draw label with confidence
            label = f"Person {conf:.2f}"
            label_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            y1_label = max(y1, label_size[1] + 10)
            
            # Draw label background
            cv2.rectangle(frame, 
                         (x1, y1_label - label_size[1] - 10),
                         (x1 + label_size[0], y1_label + baseline - 10),
                         color, -1)
            
            # Draw label text
            cv2.putText(frame, label, (x1, y1_label - 7),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame



