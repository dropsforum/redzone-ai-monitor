"""
AI Detection Engine for the native Mac desktop app.

Uses Ultralytics directly so the packaged Mac app keeps the fast Python/OpenCV
path instead of the browser ONNX Runtime path.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
import os
import numpy as np
from pathlib import Path
from typing import Any, List, NamedTuple, Optional, Tuple


class TrackedDetection(NamedTuple):
    """One person detection with an ID scoped to the current detector session."""

    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    track_id: int


@dataclass(frozen=True)
class InferenceHealth:
    backend: str
    preprocess_ms: float
    inference_ms: float
    postprocess_ms: float
    total_ms: float
    detector_errors: int


class AIDetector:
    """AI-powered person detection using Ultralytics YOLO"""
    
    # COCO dataset class names (YOLO is trained on COCO)
    # Person class is index 0
    PERSON_CLASS_ID = 0
    
    def __init__(
        self,
        model_name: str = "yolo26n.pt",
        confidence_threshold: float = 0.5,
        imgsz: int = 640,
        device: str = "auto",
        backend: str = "pytorch",
    ):
        """
        Initialize the AI detector
        Args:
            model_name: YOLO model size (n=nano, s=small, m=medium, l=large)
            confidence_threshold: Minimum confidence for detections (0-1)
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.imgsz = imgsz
        self.requested_device = device
        self.device = device if device and device != "auto" else "auto"
        self.backend = backend if backend in {"pytorch", "coreml"} else "pytorch"
        self.model: Optional[Any] = None
        self.is_loaded = False
        self.model_version = "unknown"
        self._inference_lock = threading.RLock()
        self._raw_to_session_track: dict[int, int] = {}
        self._next_session_track_id = 1
        self._untracked_boxes: list[tuple[tuple[int, int, int, int], int]] = []
        self.detector_errors = 0
        self.last_health = InferenceHealth(
            backend=self.backend_name,
            preprocess_ms=0.0,
            inference_ms=0.0,
            postprocess_ms=0.0,
            total_ms=0.0,
            detector_errors=0,
        )

    @property
    def backend_name(self) -> str:
        return "coreml" if self.backend == "coreml" else f"pytorch/{self.device}"

    def _resolve_device(self, requested: str) -> str:
        if requested and requested != "auto":
            return requested
        try:
            import torch
        except Exception:
            return "cpu"
        if torch is not None and getattr(torch.backends, "mps", None):
            if torch.backends.mps.is_available():
                return "mps"
        return "cpu"
        
    def load_model(self) -> bool:
        """Load the YOLO model"""
        try:
            from ultralytics import YOLO
            from ultralytics import __version__ as ultralytics_version

            model_ref = self._resolve_model_ref()
            self.device = (
                "coreml"
                if self.backend == "coreml"
                else self._resolve_device(self.requested_device)
            )
            print(f"Loading YOLO model: {model_ref} on {self.device}...")
            self.model = YOLO(model_ref)
            self.model_version = ultralytics_version
            # A tiny warmup makes the first monitored frame less surprising.
            warmup = np.zeros((self.imgsz, self.imgsz, 3), dtype=np.uint8)
            self.model.predict(warmup, **self._inference_options())
            self.reset_tracker()
            self.is_loaded = True
            print(f"✓ YOLO model loaded successfully")
            return True
        except Exception as e:
            self.detector_errors += 1
            print(f"✗ Error loading YOLO model: {e}")
            return False

    def _resolve_model_ref(self) -> str:
        model_path = Path(self.model_name).expanduser()
        if self.backend == "coreml":
            if model_path.suffix in {".mlpackage", ".mlmodel", ".mlmodelc"}:
                if model_path.exists():
                    return str(model_path)
                raise FileNotFoundError(f"CoreML model not found: {model_path}")

            configured_path = os.environ.get("REDZONE_COREML_MODEL")
            coreml_path = (
                Path(configured_path).expanduser()
                if configured_path
                else Path.home()
                / "Library"
                / "Caches"
                / "redzone-ai-monitor"
                / "yolo26n-exports"
                / "yolo26n.mlpackage"
            )
            if coreml_path.exists():
                return str(coreml_path)
            raise FileNotFoundError(
                "CoreML backend requires an external yolo26n.mlpackage. "
                "Pass --model /path/to/yolo26n.mlpackage or set "
                "REDZONE_COREML_MODEL."
            )
        if model_path.exists():
            return str(model_path)
        if model_path.parent == Path("."):
            bundled_model = Path.cwd() / "models" / self.model_name
            if bundled_model.exists():
                return str(bundled_model)
        return self.model_name

    def _inference_options(self) -> dict[str, Any]:
        options: dict[str, Any] = {
            "verbose": False,
            "conf": self.confidence_threshold,
            "imgsz": self.imgsz,
            "classes": [self.PERSON_CLASS_ID],
        }
        if self.backend == "pytorch":
            options["device"] = self.device
        return options
    
    def detect_people(self, frame: np.ndarray) -> List[TrackedDetection]:
        """
        Track people in the frame with ByteTrack.

        Ultralytics tracker IDs are mapped to a compact ID sequence that starts
        at 1 whenever reset_tracker() is called.

        Args:
            frame: Input image (BGR format from OpenCV)
        Returns:
            List of tracked person detections.
        """
        if not self.is_loaded or self.model is None:
            return []
        
        try:
            with self._inference_lock:
                started = time.perf_counter()
                results = self.model.track(
                    frame,
                    persist=True,
                    tracker="bytetrack.yaml",
                    **self._inference_options(),
                )

                detections: list[TrackedDetection] = []
                speed_totals = {"preprocess": 0.0, "inference": 0.0, "postprocess": 0.0}
                speed_samples = 0

                for result in results:
                    speed = getattr(result, "speed", None) or {}
                    for key in speed_totals:
                        speed_totals[key] += float(speed.get(key, 0.0) or 0.0)
                    speed_samples += 1

                    for box in result.boxes:
                        class_id = int(box.cls[0])
                        if class_id != self.PERSON_CLASS_ID:
                            continue

                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        bbox = (int(x1), int(y1), int(x2), int(y2))
                        confidence = float(box.conf[0])
                        raw_track_id = self._box_track_id(box)
                        session_track_id = self._session_track_id(raw_track_id, bbox)
                        detections.append(TrackedDetection(
                            *bbox,
                            confidence,
                            session_track_id,
                        ))

                divisor = max(1, speed_samples)
                self.last_health = InferenceHealth(
                    backend=self.backend_name,
                    preprocess_ms=speed_totals["preprocess"] / divisor,
                    inference_ms=speed_totals["inference"] / divisor,
                    postprocess_ms=speed_totals["postprocess"] / divisor,
                    total_ms=(time.perf_counter() - started) * 1000.0,
                    detector_errors=self.detector_errors,
                )
                self._untracked_boxes = [
                    ((d.x1, d.y1, d.x2, d.y2), d.track_id)
                    for d in detections
                    if self._raw_id_for_session_id(d.track_id) is None
                ]
                return detections
            
        except Exception as e:
            self.detector_errors += 1
            self.last_health = InferenceHealth(
                backend=self.backend_name,
                preprocess_ms=0.0,
                inference_ms=0.0,
                postprocess_ms=0.0,
                total_ms=0.0,
                detector_errors=self.detector_errors,
            )
            print(f"✗ Error during detection: {e}")
            return []

    @staticmethod
    def _box_track_id(box: Any) -> Optional[int]:
        value = getattr(box, "id", None)
        if value is None:
            return None
        try:
            scalar = value[0]
            item = getattr(scalar, "item", None)
            return int(item() if callable(item) else scalar)
        except (IndexError, RuntimeError, TypeError, ValueError):
            try:
                return int(value)
            except (RuntimeError, TypeError, ValueError):
                return None

    def _session_track_id(
        self,
        raw_track_id: Optional[int],
        bbox: tuple[int, int, int, int],
    ) -> int:
        if raw_track_id is not None:
            existing = self._raw_to_session_track.get(raw_track_id)
            if existing is not None:
                return existing
            assigned = self._allocate_session_track_id()
            self._raw_to_session_track[raw_track_id] = assigned
            return assigned

        # ByteTrack normally supplies an ID. This fallback preserves continuity
        # for a transient untracked result without inventing a global identity.
        best_id: Optional[int] = None
        best_iou = 0.0
        for previous_bbox, previous_id in self._untracked_boxes:
            overlap = self._bbox_iou(previous_bbox, bbox)
            if overlap > best_iou:
                best_iou = overlap
                best_id = previous_id
        return best_id if best_id is not None and best_iou >= 0.30 else self._allocate_session_track_id()

    def _allocate_session_track_id(self) -> int:
        track_id = self._next_session_track_id
        self._next_session_track_id += 1
        return track_id

    def _raw_id_for_session_id(self, session_track_id: int) -> Optional[int]:
        for raw_id, mapped_id in self._raw_to_session_track.items():
            if mapped_id == session_track_id:
                return raw_id
        return None

    @staticmethod
    def _bbox_iou(
        first: tuple[int, int, int, int],
        second: tuple[int, int, int, int],
    ) -> float:
        ax1, ay1, ax2, ay2 = first
        bx1, by1, bx2, by2 = second
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        intersection = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        first_area = max(0, ax2 - ax1) * max(0, ay2 - ay1)
        second_area = max(0, bx2 - bx1) * max(0, by2 - by1)
        union = first_area + second_area - intersection
        return intersection / union if union > 0 else 0.0

    def reset_tracker(self) -> None:
        """Reset ByteTrack state and the session-local ID mapping."""
        with self._inference_lock:
            predictor = getattr(self.model, "predictor", None) if self.model is not None else None
            trackers = getattr(predictor, "trackers", None) if predictor is not None else None
            if trackers:
                for tracker in trackers:
                    reset = getattr(tracker, "reset", None)
                    if callable(reset):
                        reset()
            if predictor is not None and hasattr(predictor, "vid_path"):
                vid_path = getattr(predictor, "vid_path")
                if isinstance(vid_path, list):
                    predictor.vid_path = [None] * len(vid_path)
            self._raw_to_session_track.clear()
            self._untracked_boxes.clear()
            self._next_session_track_id = 1
    
    def draw_detections(self, frame: np.ndarray, detections: List[TrackedDetection],
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
        import cv2

        for x1, y1, x2, y2, conf, track_id in detections:
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
            
            # Draw label with confidence
            label = f"Person #{track_id} {conf:.2f}"
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
