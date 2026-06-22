"""
Native Qt front end for the DROPS Red Zone Monitoring Mac app.

This UI mirrors the web application while keeping the fast Python/OpenCV/
Ultralytics inference path.
"""

from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import cv2
import numpy as np
from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QFont, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .ai_detector import AIDetector
from .alert_system import AlertSystem
from .camera_manager import CameraManager
from .config import Config

Detection = Tuple[int, int, int, int, float]
Point = Tuple[float, float]

ACCENT = "#55799a"
RED = "#dc2626"
SLATE_50 = "#f8fafc"
SLATE_100 = "#f1f5f9"
SLATE_200 = "#e2e8f0"
SLATE_400 = "#94a3b8"
SLATE_600 = "#475569"
SLATE_800 = "#1e293b"


def button(text: str, kind: str = "secondary") -> QPushButton:
    btn = QPushButton(text)
    btn.setMinimumHeight(34)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setProperty("kind", kind)
    return btn


class VideoPanel(QFrame):
    def __init__(
        self,
        on_file_drop: Callable[[Path], None],
        on_fullscreen: Callable[[], None],
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.on_file_drop = on_file_drop
        self.on_fullscreen = on_fullscreen
        self.source_mode = "camera"
        self.video_label = ""
        self.frame: Optional[np.ndarray] = None
        self.detections: List[Detection] = []
        self.zone: List[Point] = []
        self.is_drawing = False
        self.is_monitoring = False
        self.is_fullscreen = False
        self.traffic = "green"
        self.ai_status = "Initializing AI"
        self.drag_active = False
        self.setAcceptDrops(True)
        self.setMinimumSize(640, 360)
        policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(
            f"background:{SLATE_50}; border:1px solid {SLATE_200}; border-radius:12px;"
        )

    def sizeHint(self):  # noqa: N802 - Qt API
        return QSize(700, 394)

    def hasHeightForWidth(self):  # noqa: N802 - Qt API
        return True

    def heightForWidth(self, width: int):  # noqa: N802 - Qt API
        return max(360, int(width * 9 / 16))

    def set_state(
        self,
        *,
        source_mode: Optional[str] = None,
        video_label: Optional[str] = None,
        frame: Optional[np.ndarray] = None,
        detections: Optional[List[Detection]] = None,
        zone: Optional[List[Point]] = None,
        is_drawing: Optional[bool] = None,
        is_monitoring: Optional[bool] = None,
        is_fullscreen: Optional[bool] = None,
        traffic: Optional[str] = None,
        ai_status: Optional[str] = None,
    ):
        if source_mode is not None:
            self.source_mode = source_mode
        if video_label is not None:
            self.video_label = video_label
        if frame is not None:
            self.frame = frame
        if detections is not None:
            self.detections = detections
        if zone is not None:
            self.zone = zone
        if is_drawing is not None:
            self.is_drawing = is_drawing
        if is_monitoring is not None:
            self.is_monitoring = is_monitoring
        if is_fullscreen is not None:
            self.is_fullscreen = is_fullscreen
        if traffic is not None:
            self.traffic = traffic
        if ai_status is not None:
            self.ai_status = ai_status
        self.update()

    def frame_rect(self) -> QRectF:
        panel = QRectF(0, 0, self.width(), self.height())
        if self.frame is None:
            return panel
        h, w = self.frame.shape[:2]
        if not w or not h:
            return panel
        fit_cover = self.source_mode == "camera"
        scale = max(panel.width() / w, panel.height() / h) if fit_cover else min(panel.width() / w, panel.height() / h)
        draw_w = w * scale
        draw_h = h * scale
        return QRectF((panel.width() - draw_w) / 2, (panel.height() - draw_h) / 2, draw_w, draw_h)

    def normalized_from_event(self, event) -> Optional[Point]:
        rect = self.frame_rect()
        if not rect.contains(event.position()):
            return None
        x = (event.position().x() - rect.left()) / rect.width()
        y = (event.position().y() - rect.top()) / rect.height()
        return max(0.0, min(1.0, x)), max(0.0, min(1.0, y))

    def mousePressEvent(self, event):  # noqa: N802 - Qt API
        if event.button() == Qt.MouseButton.LeftButton and self.fullscreen_button_rect().contains(event.position()):
            self.on_fullscreen()
            event.accept()
            return
        if self.is_drawing and event.button() == Qt.MouseButton.LeftButton:
            point = self.normalized_from_event(event)
            if point is not None:
                self.zone.append(point)
                self.update()
        super().mousePressEvent(event)

    def dragEnterEvent(self, event):  # noqa: N802 - Qt API
        if self.source_mode == "file" and event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drag_active = True
            self.update()

    def dragLeaveEvent(self, event):  # noqa: N802 - Qt API
        self.drag_active = False
        self.update()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):  # noqa: N802 - Qt API
        self.drag_active = False
        if self.source_mode == "file":
            for url in event.mimeData().urls():
                path = Path(url.toLocalFile())
                if path.suffix.lower() in {".mp4", ".mov", ".m4v", ".webm", ".ogv", ".ogg", ".avi"}:
                    self.on_file_drop(path)
                    break
        self.update()

    def paintEvent(self, event):  # noqa: N802 - Qt API
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(SLATE_50))
        frame_rect = self.frame_rect()

        if self.frame is None:
            self._paint_empty(painter)
        else:
            rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            h, w = rgb.shape[:2]
            image = QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888)
            pix = QPixmap.fromImage(image.copy())
            painter.drawPixmap(frame_rect, pix, QRectF(0, 0, w, h))
            self._paint_source_badge(painter)
            self._paint_zone(painter, frame_rect)
            self._paint_detections(painter, frame_rect)

        if self.is_monitoring:
            self._paint_traffic(painter)
        self._paint_fullscreen_button(painter)
        if self.drag_active:
            painter.fillRect(self.rect(), QColor(85, 121, 154, 35))
            self._center_text(painter, "Drop Video", QColor(ACCENT))

    def _paint_empty(self, painter: QPainter):
        if self.source_mode == "file":
            self._center_text(painter, "Choose Recorded Video", QColor(SLATE_800), "☁")
        else:
            self._center_text(painter, self.ai_status or "Opening Camera", QColor(SLATE_600), "●")

    def _center_text(self, painter: QPainter, text: str, color: QColor, icon: str = ""):
        painter.setPen(color)
        font = QFont()
        font.setBold(True)
        font.setPointSize(13)
        font.setCapitalization(QFont.Capitalization.AllUppercase)
        painter.setFont(font)
        if icon:
            icon_font = QFont()
            icon_font.setPointSize(40)
            painter.setFont(icon_font)
            painter.drawText(self.rect().adjusted(0, -54, 0, 0), Qt.AlignmentFlag.AlignCenter, icon)
            painter.setFont(font)
        painter.drawText(self.rect().adjusted(0, 32, 0, 0), Qt.AlignmentFlag.AlignCenter, text)

    def _paint_source_badge(self, painter: QPainter):
        label = "LIVE STREAM" if self.source_mode == "camera" else (self.video_label or "RECORDED VIDEO").upper()
        badge = QRectF(16, 16, min(max(150, len(label) * 8 + 34), self.width() - 32), 28)
        painter.setPen(QPen(QColor(SLATE_200), 1))
        painter.setBrush(QColor(255, 255, 255, 220))
        painter.drawRoundedRect(badge, 14, 14)
        painter.setPen(QColor(SLATE_600))
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(badge.adjusted(16, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter, label)

    def _to_panel(self, point: Point, rect: QRectF) -> QPointF:
        return QPointF(rect.left() + point[0] * rect.width(), rect.top() + point[1] * rect.height())

    def _paint_zone(self, painter: QPainter, rect: QRectF):
        if not self.zone:
            return
        points = [self._to_panel(p, rect) for p in self.zone]
        pen = QPen(QColor(RED), 4)
        if self.is_drawing:
            pen.setDashPattern([5, 5])
        painter.setPen(pen)
        painter.setBrush(QColor(220, 38, 38, 76) if len(points) >= 3 and not self.is_drawing else Qt.BrushStyle.NoBrush)
        if len(points) >= 3 and not self.is_drawing:
            painter.drawPolygon(points)
        else:
            for idx in range(len(points) - 1):
                painter.drawLine(points[idx], points[idx + 1])
        if self.is_drawing:
            painter.setPen(QPen(QColor(RED), 2))
            painter.setBrush(QColor("white"))
            for p in points:
                painter.drawEllipse(p, 6, 6)

    def _paint_detections(self, painter: QPainter, rect: QRectF):
        if self.frame is None:
            return
        h, w = self.frame.shape[:2]
        sx = rect.width() / w
        sy = rect.height() / h
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        for x1, y1, x2, y2, conf in self.detections:
            box = QRectF(rect.left() + x1 * sx, rect.top() + y1 * sy, (x2 - x1) * sx, (y2 - y1) * sy)
            painter.setPen(QPen(QColor(RED), 2))
            painter.setBrush(QColor(220, 38, 38, 32))
            painter.drawRect(box)
            label = f"Person {round(conf * 100)}%"
            label_rect = QRectF(box.left(), max(rect.top(), box.top() - 24), 82, 22)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(RED))
            painter.drawRoundedRect(label_rect, 5, 5)
            painter.setPen(QColor("white"))
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label)

    def _paint_traffic(self, painter: QPainter):
        box = QRectF(self.width() - 58, self.height() - 118, 42, 102)
        painter.setPen(QPen(QColor(SLATE_200), 1))
        painter.setBrush(QColor(255, 255, 255, 230))
        painter.drawRoundedRect(box, 12, 12)
        for idx, color in enumerate(["red", "yellow", "green"]):
            active = self.traffic == color
            qcolor = QColor({"red": "#ef4444", "yellow": "#eab308", "green": "#22c55e"}[color])
            if not active:
                qcolor.setAlpha(85)
            center = QPointF(box.center().x(), box.top() + 20 + idx * 31)
            painter.setPen(QPen(qcolor.lighter(110) if active else QColor("#64748b"), 2))
            painter.setBrush(qcolor)
            painter.drawEllipse(center, 7, 7)

    def fullscreen_button_rect(self) -> QRectF:
        return QRectF(self.width() - 148, 16, 132, 34)

    def _paint_fullscreen_button(self, painter: QPainter):
        rect = self.fullscreen_button_rect()
        painter.setPen(QPen(QColor(SLATE_200), 1))
        painter.setBrush(QColor(255, 255, 255, 230))
        painter.drawRoundedRect(rect, 10, 10)
        painter.setPen(QColor(ACCENT))
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        label = "EXIT FULL SCREEN" if self.is_fullscreen else "FULL SCREEN"
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, label)


class RedZoneQtWindow(QMainWindow):
    def __init__(self, initial_video: Optional[Path] = None, camera_index: Optional[int] = None):
        super().__init__()
        self.config = Config()
        self.camera = CameraManager(
            camera_index=self.config.get("camera_index", 0),
            width=self.config.get("camera_width", 1280),
            height=self.config.get("camera_height", 720),
            fps=self.config.get("camera_fps", 15),
            source_type=self.config.get("video_source", "camera"),
            video_path=self.config.get("video_file_path", ""),
        )
        self.detector = AIDetector(
            model_name=self.config.get("model_size", "yolo26n.pt"),
            confidence_threshold=float(self.config.get("confidence_threshold", 0.5)),
            imgsz=int(self.config.get("model_imgsz", 640)),
            device=self.config.get("model_device", "auto"),
        )
        self.alert = AlertSystem(cooldown_seconds=int(self.config.get("alert_cooldown", 5)))
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.load_future: Optional[Future] = None
        self.detect_future: Optional[Future] = None
        self.current_frame: Optional[np.ndarray] = None
        self.detections: List[Detection] = []
        self.zone: List[Point] = []
        self.source_mode = "camera"
        self.video_path: Optional[Path] = None
        self.is_monitoring = False
        self.is_drawing = False
        self.audio_enabled = True
        self.traffic = "green"
        self.warning_buffer = 0.10
        self.frame_count = 0
        self.last_fps = time.monotonic()
        self.last_detection_at = 0.0
        self.fps = 0
        self.is_video_fullscreen = False
        self._normal_geometry = None

        self.setWindowTitle("DROPS Red Zone Monitoring")
        self.resize(760, 980)
        self._build_ui()
        self._load_zone()
        if camera_index is not None:
            self.camera.camera_index = camera_index
            self.config.set("camera_index", camera_index)
        if initial_video is not None:
            self.video_path = initial_video.expanduser()
            self.camera.video_path = self.video_path
            self.camera.source_type = "video"
            self.config.set("video_source", "video")
            self.config.set("video_file_path", str(self.video_path))
        self._set_source_mode(self.camera.source_type)
        self._start_ai_loading()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(16)

    def _build_ui(self):
        self._build_menu()
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(10, 10, 10, 10)
        self.root_layout = outer

        content = QWidget()
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        outer.addWidget(content, 1)
        layout = QVBoxLayout(content)
        layout.setSpacing(8)
        self.content_layout = layout

        self.header_widget = QWidget()
        header = QHBoxLayout(self.header_widget)
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        title = QLabel("DROPS RED ZONE")
        title.setObjectName("title")
        subtitle = QLabel("⚡ YOLO26 AI • PYTHON-NATIVE")
        subtitle.setObjectName("subtitle")
        self.live_btn = QPushButton("▣ LIVE")
        self.recorded_btn = QPushButton("▣ RECORDED")
        self.live_btn.clicked.connect(lambda: self._set_source_mode("camera"))
        self.recorded_btn.clicked.connect(lambda: self._set_source_mode("video"))
        self.choose_btn = QPushButton("☁ VIDEO")
        self.choose_btn.clicked.connect(self._choose_video)
        self.fps_label = QLabel("▭ 0 FPS")
        self.fps_label.setObjectName("metric")
        self.audio_check = QCheckBox("Audio")
        self.audio_check.setChecked(True)
        self.audio_check.toggled.connect(lambda checked: setattr(self, "audio_enabled", checked))
        self.ai_chip = QLabel("Loading...")
        self.ai_chip.setObjectName("chip")
        header.addWidget(title)
        header.addWidget(subtitle)
        header.addStretch(1)
        header.addWidget(self.live_btn)
        header.addWidget(self.recorded_btn)
        header.addWidget(self.choose_btn)
        header.addWidget(self.fps_label)
        header.addWidget(self.audio_check)
        header.addWidget(self.ai_chip)
        layout.addWidget(self.header_widget)

        self.video_panel = VideoPanel(self._load_video_file, self._toggle_video_fullscreen)
        layout.addWidget(self.video_panel, 1)

        self.control_bar = QFrame()
        self.control_bar.setObjectName("controlBar")
        self.control_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.control_bar.setMaximumHeight(74)
        controls = QHBoxLayout(self.control_bar)
        controls.setContentsMargins(8, 8, 8, 8)
        controls.setSpacing(8)

        self.monitor_btn = button("▶ START", "primary")
        self.draw_btn = button("✎ ZONE", "outline")
        self.reset_zone_btn = button("↺ RESET")
        self.screenshot_btn = button("▣ SHOT")
        self.sound_btn = button("🔊 SOUND", "yellow")
        self.fullscreen_btn = button("⛶ FULL")
        self.monitor_btn.clicked.connect(self._toggle_monitor)
        self.draw_btn.clicked.connect(self._toggle_drawing)
        self.reset_zone_btn.clicked.connect(self._reset_zone)
        self.screenshot_btn.clicked.connect(self._screenshot)
        self.sound_btn.clicked.connect(lambda: self.alert.trigger_alert())
        self.fullscreen_btn.clicked.connect(self._toggle_video_fullscreen)

        for widget in [self.monitor_btn, self.draw_btn, self.reset_zone_btn, self.screenshot_btn, self.sound_btn, self.fullscreen_btn]:
            controls.addWidget(widget)

        sens = QWidget()
        sens.setObjectName("compactGroup")
        sens.setMaximumWidth(300)
        sens_layout = QHBoxLayout(sens)
        sens_layout.setContentsMargins(8, 0, 8, 0)
        sens_layout.setSpacing(8)
        sens_label = QLabel("⚡ Sensitivity")
        sens_label.setObjectName("compactLabel")
        self.sens_value = QLabel("10%")
        self.sens_value.setObjectName("metric")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(1, 30)
        self.slider.setValue(10)
        self.slider.valueChanged.connect(self._set_warning)
        sens_layout.addWidget(sens_label)
        sens_layout.addWidget(self.sens_value)
        sens_layout.addWidget(self.slider, 1)
        controls.addWidget(sens, 1)

        self.info_stack = QStackedWidget()
        self.info_stack.setMaximumWidth(330)
        self.info_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        cam = QWidget()
        cam_layout = QHBoxLayout(cam)
        cam_layout.setContentsMargins(0, 0, 0, 0)
        cam_layout.setSpacing(8)
        cam_label = QLabel("⚙ Camera")
        cam_label.setObjectName("compactLabel")
        self.camera_combo = QComboBox()
        self.camera_combo.setMinimumWidth(120)
        self.camera_combo.addItem("Camera 0", 0)
        self.camera_combo.currentIndexChanged.connect(self._camera_changed)
        refresh = QPushButton("↻")
        refresh.setToolTip("Refresh cameras")
        refresh.clicked.connect(self._refresh_cameras)
        cam_layout.addWidget(cam_label)
        cam_layout.addWidget(self.camera_combo, 1)
        cam_layout.addWidget(refresh)
        rec = QWidget()
        rec_layout = QHBoxLayout(rec)
        rec_layout.setContentsMargins(0, 0, 0, 0)
        rec_layout.setSpacing(8)
        self.recorded_info = QLabel("No video selected")
        self.recorded_info.setObjectName("compactLabel")
        choose2 = QPushButton("☁")
        choose2.setToolTip("Choose recorded video")
        choose2.clicked.connect(self._choose_video)
        rec_layout.addWidget(QLabel("▣ Video"))
        rec_layout.addWidget(choose2)
        rec_layout.addWidget(self.recorded_info, 1)
        self.info_stack.addWidget(cam)
        self.info_stack.addWidget(rec)
        controls.addWidget(self.info_stack)
        layout.addWidget(self.control_bar)

        self.setStyleSheet(f"""
            QWidget {{ background: white; color: {SLATE_800}; font-family: "Arial"; }}
            QLabel#title {{ color: {ACCENT}; font-size: 17px; font-weight: 900; font-style: italic; }}
            QLabel#subtitle {{ color: {SLATE_400}; font-size: 9px; font-weight: 800; }}
            QLabel#metric {{ color:{SLATE_800}; font-size:11px; font-weight:800; }}
            QLabel#compactLabel {{ color:{SLATE_400}; font-size:10px; font-weight:900; }}
            QLabel#chip {{ background:{SLATE_50}; border:1px solid {SLATE_200}; border-radius:8px; padding:4px 8px; color:{SLATE_600}; font-size:10px; font-weight:800; }}
            QPushButton {{ border:1px solid {SLATE_200}; border-radius:8px; background:white; color:{ACCENT}; padding:5px 10px; font-size:10px; font-weight:900; }}
            QPushButton[kind="primary"] {{ background:{ACCENT}; color:white; border-color:{ACCENT}; }}
            QPushButton[kind="outline"] {{ background:white; color:{ACCENT}; border:2px solid {ACCENT}; }}
            QPushButton[kind="yellow"] {{ background:#eab308; color:white; border-color:#eab308; }}
            QPushButton:disabled {{ background:{SLATE_100}; color:{SLATE_400}; border-color:{SLATE_200}; }}
            QFrame#controlBar {{ background:{SLATE_50}; border:1px solid {SLATE_100}; border-radius:10px; }}
            QFrame#card {{ background:white; border:1px solid {SLATE_100}; border-radius:16px; }}
            QSlider::groove:horizontal {{ height:6px; background:{SLATE_100}; border-radius:3px; }}
            QSlider::handle:horizontal {{ background:{ACCENT}; width:18px; margin:-6px 0; border-radius:9px; }}
            QComboBox {{ background:white; border:1px solid {SLATE_100}; border-radius:8px; padding:5px 8px; font-size:10px; }}
        """)

    def _build_menu(self):
        view_menu = self.menuBar().addMenu("View")
        self.fullscreen_action = QAction("Enter Video Full Screen", self)
        self.fullscreen_action.setShortcut("F")
        self.fullscreen_action.triggered.connect(self._toggle_video_fullscreen)
        view_menu.addAction(self.fullscreen_action)

    def _toggle_video_fullscreen(self):
        self._set_video_fullscreen(not self.is_video_fullscreen)

    def _set_video_fullscreen(self, enabled: bool):
        if enabled == self.is_video_fullscreen:
            return
        self.is_video_fullscreen = enabled
        self.video_panel.set_state(is_fullscreen=enabled)
        self.fullscreen_action.setText("Exit Video Full Screen" if enabled else "Enter Video Full Screen")
        if enabled:
            self._normal_geometry = self.geometry()
            self.header_widget.setVisible(False)
            self.control_bar.setVisible(False)
            self.root_layout.setContentsMargins(0, 0, 0, 0)
            self.content_layout.setSpacing(0)
            self.video_panel.setStyleSheet("background:black; border:0; border-radius:0;")
            self.showFullScreen()
        else:
            self.header_widget.setVisible(True)
            self.control_bar.setVisible(True)
            self.root_layout.setContentsMargins(10, 10, 10, 10)
            self.content_layout.setSpacing(8)
            self.video_panel.setStyleSheet(
                f"background:{SLATE_50}; border:1px solid {SLATE_200}; border-radius:12px;"
            )
            self.showNormal()
            if self._normal_geometry is not None:
                self.setGeometry(self._normal_geometry)
            self._normal_geometry = None

    def keyPressEvent(self, event):  # noqa: N802 - Qt API
        if event.key() == Qt.Key.Key_Escape and self.is_video_fullscreen:
            self._set_video_fullscreen(False)
            return
        if event.key() == Qt.Key.Key_F:
            self._toggle_video_fullscreen()
            return
        super().keyPressEvent(event)

    def _card(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        label = QLabel(title)
        label.setStyleSheet(f"color:{SLATE_400}; font-size:10px; font-weight:900;")
        layout.addWidget(label)
        return frame

    def _load_zone(self):
        if self.config.zone_points:
            self.zone = [(x / max(1, self.camera.width), y / max(1, self.camera.height)) for x, y in self.config.zone_points]

    def _start_ai_loading(self):
        self.ai_chip.setText("Loading...")
        self.video_panel.set_state(ai_status="Initializing AI")
        self.load_future = self.executor.submit(self.detector.load_model)

    def _set_warning(self, value: int):
        self.warning_buffer = value / 100.0
        self.sens_value.setText(f"{value}%")

    def _refresh_cameras(self):
        current_source = self.camera.source_type
        self.camera.source_type = "camera"
        cameras = self.camera.enumerate_cameras()
        self.camera.source_type = current_source
        self.camera_combo.clear()
        for idx in cameras or [0]:
            self.camera_combo.addItem(f"Camera {idx}", idx)

    def _camera_changed(self):
        if self.source_mode != "camera":
            return
        idx = self.camera_combo.currentData()
        if idx is not None and idx != self.camera.camera_index:
            self.camera.switch_camera(int(idx))

    def _set_source_mode(self, mode: str):
        source = "video" if mode == "file" else mode
        if source not in {"camera", "video"}:
            source = "camera"
        self._reset_runtime()
        self.is_drawing = False
        self.source_mode = "file" if source == "video" else "camera"
        self.info_stack.setCurrentIndex(1 if self.source_mode == "file" else 0)
        self.choose_btn.setVisible(self.source_mode == "file")
        self.live_btn.setStyleSheet("background:white;" if self.source_mode != "camera" else f"background:white;color:{ACCENT};")
        self.recorded_btn.setStyleSheet("background:white;" if self.source_mode != "file" else f"background:white;color:{ACCENT};")
        self.camera.stop()
        self.camera.source_type = source
        if source == "camera":
            self.video_path = None
            self.recorded_info.setText("No video selected")
        elif self.video_path is not None:
            self.camera.video_path = self.video_path
        self.camera.start()
        self.video_panel.set_state(source_mode=self.source_mode, video_label=self.video_path.name if self.video_path else "")
        self._sync_controls()

    def _load_video_file(self, path: Path):
        self.video_path = path
        self.camera.video_path = path
        self.config.set("video_source", "video")
        self.config.set("video_file_path", str(path))
        self.recorded_info.setText(path.name)
        self._set_source_mode("video")

    def _choose_video(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Recorded Video",
            str(Path.home()),
            "Videos (*.mp4 *.mov *.m4v *.webm *.ogv *.ogg *.avi);;All Files (*)",
        )
        if file_name:
            self._load_video_file(Path(file_name))

    def _toggle_monitor(self):
        if not self.detector.is_loaded or len(self.zone) < 3 or self.current_frame is None:
            return
        self.is_monitoring = not self.is_monitoring
        if self.source_mode == "file":
            if self.is_monitoring:
                self.camera.start_playback(restart=True)
            else:
                self.camera.pause_playback()
        if not self.is_monitoring:
            self.traffic = "green"
        self._sync_controls()

    def _toggle_drawing(self):
        if self.current_frame is None:
            return
        self.is_drawing = not self.is_drawing
        if self.is_drawing:
            self.is_monitoring = False
            if self.source_mode == "file":
                self.camera.pause_playback()
        else:
            self.zone = self.video_panel.zone
        self._sync_controls()

    def _reset_zone(self):
        self.is_monitoring = False
        self.is_drawing = False
        if self.source_mode == "file":
            self.camera.pause_playback()
        self.zone = []
        self.detections = []
        self.traffic = "green"
        self.config.zone_points = []
        self.config.save()
        self.video_panel.set_state(
            zone=[],
            detections=[],
            is_drawing=False,
            is_monitoring=False,
            traffic="green",
        )
        self._sync_controls()

    def _reset_runtime(self):
        self.is_monitoring = False
        self.detections = []
        self.traffic = "green"
        self.fps = 0
        self.frame_count = 0
        self.current_frame = None

    def _sync_controls(self):
        ready = self.detector.is_loaded
        has_source = self.current_frame is not None or self.camera.is_open
        can_monitor = ready and len(self.zone) >= 3 and has_source
        self.monitor_btn.setEnabled(can_monitor)
        self.monitor_btn.setText("■ STOP" if self.is_monitoring else "▶ START")
        self.draw_btn.setEnabled(has_source)
        self.draw_btn.setText("✓ SAVE" if self.is_drawing else "✎ ZONE")
        self.reset_zone_btn.setEnabled(bool(self.zone) or self.is_drawing)
        self.screenshot_btn.setEnabled(self.current_frame is not None)

    def _tick(self):
        if self.load_future is not None and self.load_future.done():
            self.load_future.result()
            self.load_future = None
            self.ai_chip.setText("AI Ready" if self.detector.is_loaded else "AI Failed")
            self._sync_controls()

        ret, frame = self.camera.read_frame()
        if ret and frame is not None:
            self.current_frame = frame
            self.frame_count += 1
            now = time.monotonic()
            if now - self.last_fps >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_fps = now
                self.fps_label.setText(f"▭  {self.fps} FPS")
            self._maybe_detect(frame)

        self.video_panel.set_state(
            source_mode=self.source_mode,
            video_label=self.video_path.name if self.video_path else "",
            frame=self.current_frame,
            detections=self.detections,
            zone=self.zone,
            is_drawing=self.is_drawing,
            is_monitoring=self.is_monitoring,
            traffic=self.traffic,
            ai_status="AI Ready" if self.detector.is_loaded else "Initializing AI",
        )
        self.zone = self.video_panel.zone
        self._sync_controls()

    def _maybe_detect(self, frame: np.ndarray):
        now = time.monotonic()
        if not self.is_monitoring or not self.detector.is_loaded or len(self.zone) < 3:
            self.detections = []
            self.traffic = "green"
            return
        if self.detect_future is not None and self.detect_future.done():
            self.detections = self.detect_future.result()
            self._evaluate_alerts(frame)
            self.detect_future = None
        if self.detect_future is None and now - self.last_detection_at >= 0.10:
            self.last_detection_at = now
            self.detect_future = self.executor.submit(self.detector.detect_people, frame.copy())

    def _evaluate_alerts(self, frame: np.ndarray):
        if not self.detections:
            self.traffic = "green"
            return
        h, w = frame.shape[:2]
        abs_zone = [(int(x * w), int(y * h)) for x, y in self.zone]
        zone_mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(zone_mask, [np.array(abs_zone, np.int32).reshape((-1, 1, 2))], 255)
        red_hit = False
        yellow_hit = False
        for x1, y1, x2, y2, _ in self.detections:
            corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), ((x1 + x2) // 2, (y1 + y2) // 2)]
            if any(0 <= x < w and 0 <= y < h and zone_mask[y, x] for x, y in corners):
                red_hit = True
                break
            pad = int(max(w, h) * self.warning_buffer)
            rect_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.rectangle(rect_mask, (max(0, x1 - pad), max(0, y1 - pad)), (min(w - 1, x2 + pad), min(h - 1, y2 + pad)), 255, -1)
            if cv2.countNonZero(cv2.bitwise_and(zone_mask, rect_mask)):
                yellow_hit = True
        if red_hit:
            self.traffic = "red"
            if self.audio_enabled:
                self.alert.trigger_alert()
        else:
            self.traffic = "yellow" if yellow_hit else "green"

    def _screenshot(self):
        if self.current_frame is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot",
            str(Path.home() / f"drops-monitor-capture-{int(time.time())}.png"),
            "PNG Images (*.png)",
        )
        if not path:
            return
        frame = self.current_frame.copy()
        h, w = frame.shape[:2]
        if len(self.zone) >= 3:
            pts = np.array([(int(x * w), int(y * h)) for x, y in self.zone], np.int32)
            overlay = frame.copy()
            cv2.fillPoly(overlay, [pts.reshape((-1, 1, 2))], (38, 38, 220))
            frame = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
            cv2.polylines(frame, [pts.reshape((-1, 1, 2))], True, (38, 38, 220), 4)
        for x1, y1, x2, y2, conf in self.detections:
            cv2.rectangle(frame, (x1, y1), (x2, y2), (154, 121, 85), 3)
            label = f"PERSON {round(conf * 100)}%"
            cv2.putText(frame, label, (x1 + 5, max(18, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(frame, "powered by dropsforum.org", (w // 4, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (154, 121, 85), 2)
        cv2.imwrite(path, frame)

    def closeEvent(self, event):  # noqa: N802 - Qt API
        if self.current_frame is not None and len(self.zone) >= 3:
            h, w = self.current_frame.shape[:2]
            self.config.zone_points = [(int(x * w), int(y * h)) for x, y in self.zone]
            self.config.save()
        self.camera.stop()
        self.executor.shutdown(wait=False, cancel_futures=True)
        super().closeEvent(event)


def run_qt_app(initial_video: Optional[str] = None, camera_index: Optional[int] = None) -> int:
    app = QApplication.instance() or QApplication([])
    window = RedZoneQtWindow(
        initial_video=Path(initial_video).expanduser() if initial_video else None,
        camera_index=camera_index,
    )
    window.show()
    return app.exec()
