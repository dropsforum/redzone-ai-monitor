import sys
import tempfile
import types
import unittest
from pathlib import Path

try:
    import numpy as np
except ModuleNotFoundError:
    np = types.ModuleType("numpy")
    np.ndarray = object
    sys.modules["numpy"] = np

from ai_motion_app.ai_detector import AIDetector


class FakeTensor:
    def __init__(self, value):
        self.value = value

    def __getitem__(self, _index):
        return self

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def cpu(self):
        return self

    def numpy(self):
        return self.value


class FakeBox:
    def __init__(self, raw_track_id: int, bbox=(10, 20, 30, 60), confidence=0.9):
        self.cls = FakeTensor(0)
        self.id = FakeTensor(raw_track_id)
        self.xyxy = FakeTensor(bbox)
        self.conf = FakeTensor(confidence)


class FakeResult:
    def __init__(self, boxes):
        self.boxes = boxes
        self.speed = {"preprocess": 1.0, "inference": 2.0, "postprocess": 3.0}


class FakeTracker:
    def __init__(self):
        self.reset_count = 0

    def reset(self):
        self.reset_count += 1


class FakePredictor:
    def __init__(self):
        self.trackers = [FakeTracker()]
        self.vid_path = ["video"]


class FakeModel:
    def __init__(self):
        self.predictor = FakePredictor()
        self.calls = []
        self.raw_track_id = 42

    def track(self, frame, **kwargs):
        self.calls.append((frame, kwargs))
        return [FakeResult([FakeBox(self.raw_track_id)])]


class AIDetectorTests(unittest.TestCase):
    def test_uses_bytetrack_and_returns_session_local_ids(self):
        detector = AIDetector(device="cpu")
        detector.model = FakeModel()
        detector.is_loaded = True
        frame = object()

        first = detector.detect_people(frame)
        second = detector.detect_people(frame)

        self.assertEqual(1, first[0].track_id)
        self.assertEqual(1, second[0].track_id)
        kwargs = detector.model.calls[0][1]
        self.assertTrue(kwargs["persist"])
        self.assertEqual("bytetrack.yaml", kwargs["tracker"])
        self.assertEqual([0], kwargs["classes"])
        self.assertEqual(2.0, detector.last_health.inference_ms)

    def test_reset_restarts_session_ids_and_resets_ultralytics_tracker(self):
        detector = AIDetector(device="cpu")
        model = FakeModel()
        detector.model = model
        detector.is_loaded = True
        frame = object()

        detector.detect_people(frame)
        detector.reset_tracker()
        model.raw_track_id = 99
        after_reset = detector.detect_people(frame)

        self.assertEqual(1, after_reset[0].track_id)
        self.assertEqual(1, model.predictor.trackers[0].reset_count)
        self.assertEqual([None], model.predictor.vid_path)

    def test_coreml_backend_requires_and_resolves_an_external_package(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            model_path = Path(temporary_directory) / "yolo26n.mlpackage"
            model_path.mkdir()
            detector = AIDetector(
                model_name=str(model_path),
                backend="coreml",
                device="mps",
            )

            self.assertEqual(str(model_path), detector._resolve_model_ref())
            self.assertEqual("coreml", detector.backend_name)
            self.assertNotIn("device", detector._inference_options())


if __name__ == "__main__":
    unittest.main()
