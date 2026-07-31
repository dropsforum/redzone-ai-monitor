import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from ai_motion_app.breach_recorder import BreachRecorder
from ai_motion_app.session_store import SessionStore


class PersistenceAndReportTests(unittest.TestCase):
    def test_recovers_active_session_at_last_heartbeat(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "sessions.sqlite3"
            recorder = BreachRecorder(database)
            recorder.start(100.0, {
                "source_type": "camera",
                "model_name": "yolo26n.pt",
                "model_version": "8.4.112",
                "detector_backend": "pytorch/cpu",
                "zone": [[0.1, 0.1], [0.9, 0.1], [0.5, 0.9]],
                "settings": {"entry_confirm_ms": 300},
            })
            session_id = recorder.session_id
            recorder.update(True, 101.0)
            recorder.start_person_breach(3, 101.0, 0.8)
            recorder.heartbeat(105.0, {"backend": "pytorch/cpu"})
            recorder.close()

            recovered_store = SessionStore(database)
            session = recovered_store.session(session_id)
            segments = recovered_store.state_segments(session_id)
            people = recovered_store.person_events(session_id)
            health = recovered_store.health_summary(session_id)

            self.assertEqual("recovered", session["status"])
            self.assertEqual(105.0, session["end_time"])
            self.assertEqual(105.0, segments[-1]["end_time"])
            self.assertEqual(105.0, people[-1]["end_time"])
            self.assertEqual(1, health["sample_count"])
            self.assertEqual("pytorch/cpu", health["backend"])
            recovered_store.close()

    def test_excel_contains_all_required_sheets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            recorder = BreachRecorder(root / "sessions.sqlite3")
            recorder.start(200.0, {
                "source_type": "recorded_video",
                "model_name": "yolo26n.pt",
                "model_version": "8.4.112",
                "detector_backend": "pytorch/mps",
                "zone": [],
                "settings": {},
            })
            recorder.update(True, 201.0)
            recorder.start_person_breach(1, 201.0, 0.91)
            recorder.end_person_breach(1, 202.0, 0.94)
            recorder.update(False, 202.0)
            recorder.stop(203.0)

            report = root / "report.xlsx"
            recorder.export_excel(report, "minute")
            recorder.close()

            with zipfile.ZipFile(report) as workbook:
                xml = workbook.read("xl/workbook.xml")
            root_element = ElementTree.fromstring(xml)
            namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            names = [
                sheet.attrib["name"]
                for sheet in root_element.findall("x:sheets/x:sheet", namespace)
            ]
            self.assertEqual([
                "Records",
                "Person Breaches",
                "Aggregated Results",
                "Overall Metrics",
                "Session Metadata",
            ], names)


if __name__ == "__main__":
    unittest.main()
