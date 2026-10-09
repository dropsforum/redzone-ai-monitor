import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from ai_motion_app.qt_app import VideoPanel


class ZoneEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_panel(self, *, frame_shape=(100, 100, 3), source_mode="file"):
        panel = VideoPanel(lambda _path: None, lambda: None)
        panel.setMinimumSize(1, 1)
        panel.resize(400, 400)
        panel.set_state(
            frame=np.zeros(frame_shape, dtype=np.uint8),
            source_mode=source_mode,
            zone=[(0.2, 0.2), (0.8, 0.2), (0.8, 0.8)],
            is_drawing=True,
        )
        panel.show()
        self.app.processEvents()
        return panel

    def drag_to(self, panel, position):
        point = QPointF(position)
        event = QMouseEvent(
            QEvent.Type.MouseMove,
            point,
            point,
            Qt.MouseButton.NoButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        QApplication.sendEvent(panel, event)

    def tearDown(self):
        for widget in QApplication.topLevelWidgets():
            widget.close()
        self.app.processEvents()

    def test_drag_moves_only_the_selected_vertex(self):
        panel = self.make_panel()

        QTest.mousePress(panel, Qt.MouseButton.LeftButton, pos=QPoint(80, 80))
        self.drag_to(panel, QPoint(160, 120))
        QTest.mouseRelease(panel, Qt.MouseButton.LeftButton, pos=QPoint(160, 120))

        self.assertEqual(3, len(panel.zone))
        self.assertEqual((0.4, 0.3), panel.zone[0])
        self.assertEqual([(0.8, 0.2), (0.8, 0.8)], panel.zone[1:])

    def test_drag_clamps_to_letterboxed_frame(self):
        panel = self.make_panel(frame_shape=(200, 100, 3))

        QTest.mousePress(panel, Qt.MouseButton.LeftButton, pos=QPoint(140, 80))
        self.drag_to(panel, QPoint(-80, 450))
        QTest.mouseRelease(panel, Qt.MouseButton.LeftButton, pos=QPoint(-80, 450))

        self.assertEqual(3, len(panel.zone))
        self.assertEqual((0.0, 1.0), panel.zone[0])

    def test_drag_release_never_appends_a_point(self):
        panel = self.make_panel()

        QTest.mousePress(panel, Qt.MouseButton.LeftButton, pos=QPoint(80, 80))
        QTest.mouseRelease(panel, Qt.MouseButton.LeftButton, pos=QPoint(80, 80))

        self.assertEqual(3, len(panel.zone))

    def test_non_editing_clicks_do_not_change_zone(self):
        panel = self.make_panel()
        original_zone = list(panel.zone)
        panel.set_state(is_drawing=False)

        QTest.mousePress(panel, Qt.MouseButton.LeftButton, pos=QPoint(80, 80))
        self.drag_to(panel, QPoint(160, 120))
        QTest.mouseRelease(panel, Qt.MouseButton.LeftButton, pos=QPoint(160, 120))

        self.assertEqual(original_zone, panel.zone)

    def test_clicking_away_from_handles_adds_a_point(self):
        panel = self.make_panel()

        QTest.mouseClick(panel, Qt.MouseButton.LeftButton, pos=QPoint(200, 200))

        self.assertEqual(4, len(panel.zone))
        self.assertEqual((0.5, 0.5), panel.zone[-1])

    def test_exiting_edit_mode_cancels_an_active_drag(self):
        panel = self.make_panel()
        QTest.mousePress(panel, Qt.MouseButton.LeftButton, pos=QPoint(80, 80))
        panel.set_state(is_drawing=False)

        self.drag_to(panel, QPoint(160, 120))
        QTest.mouseRelease(panel, Qt.MouseButton.LeftButton, pos=QPoint(160, 120))

        self.assertIsNone(panel._drag_vertex_index)
        self.assertEqual((0.2, 0.2), panel.zone[0])
        self.assertEqual(Qt.CursorShape.ArrowCursor, panel.cursor().shape())

    def test_zone_replacement_cancels_an_active_drag(self):
        panel = self.make_panel()
        QTest.mousePress(panel, Qt.MouseButton.LeftButton, pos=QPoint(80, 80))
        replacement = [(0.1, 0.1), (0.7, 0.1), (0.7, 0.7)]
        panel.set_state(zone=replacement)

        self.assertIsNone(panel._drag_vertex_index)
        self.assertEqual(replacement, panel.zone)
        self.assertEqual(Qt.CursorShape.ArrowCursor, panel.cursor().shape())

    def test_drag_preserves_the_press_offset(self):
        panel = self.make_panel()

        QTest.mousePress(panel, Qt.MouseButton.LeftButton, pos=QPoint(85, 77))
        self.assertEqual((0.2, 0.2), panel.zone[0])
        self.drag_to(panel, QPoint(205, 157))
        QTest.mouseRelease(panel, Qt.MouseButton.LeftButton, pos=QPoint(205, 157))

        self.assertEqual((0.5, 0.4), panel.zone[0])

    def test_hover_uses_open_hand_only_over_a_handle(self):
        panel = self.make_panel()

        QTest.mouseMove(panel, QPoint(80, 80))
        self.assertEqual(Qt.CursorShape.OpenHandCursor, panel.cursor().shape())
        QTest.mouseMove(panel, QPoint(200, 200))
        self.assertEqual(Qt.CursorShape.ArrowCursor, panel.cursor().shape())

    def test_fullscreen_button_takes_precedence_over_zone_editing(self):
        fullscreen_requests = []
        panel = VideoPanel(lambda _path: None, lambda: fullscreen_requests.append(True))
        panel.setMinimumSize(1, 1)
        panel.resize(400, 400)
        panel.set_state(
            frame=np.zeros((100, 100, 3), dtype=np.uint8),
            source_mode="file",
            zone=[(0.2, 0.2), (0.8, 0.2), (0.8, 0.8)],
            is_drawing=True,
        )
        panel.show()
        self.app.processEvents()

        QTest.mouseClick(panel, Qt.MouseButton.LeftButton, pos=QPoint(300, 32))

        self.assertEqual([True], fullscreen_requests)
        self.assertEqual(3, len(panel.zone))


if __name__ == "__main__":
    unittest.main()
