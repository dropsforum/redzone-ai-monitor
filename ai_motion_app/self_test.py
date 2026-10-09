"""Hardware-free release smoke test of the frozen native application."""

from __future__ import annotations

import json
import os
import platform
import tempfile
import time
import traceback
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from .version import APP_VERSION


def run_self_test(output_path: Path, device: str = "auto") -> int:
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {"version": APP_VERSION, "platform": platform.system(), "success": False, "checks": []}
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        import cv2
        import numpy as np
        from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
        from PySide6.QtGui import QMouseEvent
        from PySide6.QtTest import QTest
        from PySide6.QtWidgets import QApplication

        from .ai_detector import AIDetector
        from .breach_recorder import BreachRecorder
        from .breach_state import BreachStateMachine, TrackObservation
        from .camera_manager import CameraManager
        from .qt_app import VideoPanel
        from .zone_entry import classify_person_zone

        with tempfile.TemporaryDirectory(prefix="redzone-self-test-") as temporary:
            directory = Path(temporary)
            frame = np.zeros((180, 320, 3), dtype=np.uint8)
            frame[:, :, 1] = 60
            video_path = directory / "generated.avi"
            writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"MJPG"), 24, (320, 180))
            if not writer.isOpened():
                raise RuntimeError("Synthetic video encoder could not initialize")
            for _ in range(48):
                writer.write(frame)
            writer.release()
            # Never open a camera or read the user's monitoring store.
            camera = CameraManager(source_type="video", video_path=str(video_path))
            try:
                assert camera.start(), "Synthetic recorded video could not open"
                assert not camera.playback_active
                camera.start_playback(restart=True)
                time.sleep(0.12)
                ok, decoded = camera.read_frame()
                assert ok and decoded is not None and camera.current_frame_number >= 2
                camera.pause_playback()
                assert not camera.playback_active
            finally:
                camera.stop()
            report["checks"].append("recorded-video-decoding-and-normal-speed-playback")

            application = QApplication.instance() or QApplication([])
            panel = VideoPanel(lambda _path: None, lambda: None)
            try:
                panel.setMinimumSize(1, 1)
                panel.resize(400, 400)
                panel.set_state(frame=np.zeros((100, 100, 3), dtype=np.uint8), source_mode="file", zone=[(.2, .2), (.8, .2), (.8, .8)], is_drawing=True)
                panel.show()
                application.processEvents()
                QTest.mousePress(panel, Qt.MouseButton.LeftButton, pos=QPoint(80, 80))
                position = QPointF(160, 120)
                QApplication.sendEvent(panel, QMouseEvent(QEvent.Type.MouseMove, position, position, Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier))
                QTest.mouseRelease(panel, Qt.MouseButton.LeftButton, pos=QPoint(160, 120))
                assert panel.zone[0] == (.4, .3) and len(panel.zone) == 3
                panel.set_state(is_drawing=False)
                application.processEvents()
                assert not panel.grab().toImage().isNull()
                report["checks"].append("qt-rendering-and-draggable-zone-corners")
            finally:
                panel.close()
                application.processEvents()

            zone = [(.1, .1), (.5, .1), (.5, .9), (.1, .9)]
            contact = classify_person_zone(20, 200, 180, zone, 320, 180, .1, mask_polygons=[(40, 30), (130, 30), (130, 170), (40, 170)])
            assert contact.inside and contact.method == "mask"
            machine = BreachStateMachine()
            observation = TrackObservation(1, True, True, .95)
            assert machine.update([observation], 1000).traffic == "yellow"
            assert machine.update([observation], 1000.31).traffic == "red"
            assert machine.update([], 1001.1).traffic == "green"
            report["checks"].append("silhouette-contact-entry-and-exit-grace")

            recorder = BreachRecorder(directory / "monitoring.sqlite3")
            try:
                recorder.start(1000, {"model_name": "yolo26n-seg.pt", "source_type": "synthetic"})
                recorder.update(True, 1001)
                recorder.start_person_breach(1, 1001, .95)
                recorder.update(False, 1002)
                recorder.end_person_breach(1, 1002)
                recorder.stop(1003)
                workbook = directory / "report.xlsx"
                recorder.export_excel(workbook, "minute")
                with zipfile.ZipFile(workbook) as archive:
                    tree = ElementTree.fromstring(archive.read("xl/workbook.xml"))
                    sheets = [item.attrib["name"] for item in tree.iter() if item.tag.endswith("}sheet")]
                assert sheets == ["Records", "Person Breaches", "Aggregated Results", "Overall Metrics", "Session Metadata"]
                assert recorder.summary()["breach_seconds"] == 1
            finally:
                recorder.close()
            report["checks"].append("sqlite-and-five-sheet-excel-report")

            detector = AIDetector(device=device)
            assert detector.load_model(), detector.load_error
            assert detector.model.task == "segment", "The default model must be the segmentation model"
            detector.detect_people(frame)
            assert detector.detector_errors == 0
            report["model"] = detector.model_name
            report["ultralytics"] = detector.model_version
            report["backend"] = detector.backend_name
            report["checks"].append("verified-model-download-segmentation-tracking-and-inference")
        report["success"] = True
    except Exception as error:
        report["error"] = str(error)
        traceback.print_exc()
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0 if report["success"] else 1
