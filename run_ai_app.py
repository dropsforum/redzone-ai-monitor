#!/usr/bin/env python3
"""
Launcher script for DROPS Red Zone Monitoring
"""

import sys
import os
import argparse
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def parse_args():
    parser = argparse.ArgumentParser(description="Run the native DROPS Red Zone Monitoring Mac app.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--camera", type=int, help="Use a camera index, for example --camera 0.")
    source.add_argument("--video", type=str, help="Use a recorded video file. Playback starts when monitoring starts.")
    parser.add_argument("input_video", nargs="?", help="Optional video file, including when opening a file with the app.")
    parser.add_argument("--model", type=str, help="Ultralytics model name/path. Defaults to yolo26n.pt.")
    parser.add_argument("--device", type=str, choices=["auto", "mps", "cpu"], help="Inference device.")
    parser.add_argument(
        "--backend",
        type=str,
        choices=["pytorch", "coreml"],
        help="Detector backend. PyTorch/MPS remains the production default.",
    )
    parser.add_argument("--confidence", type=float, help="Detection confidence threshold, 0.0 to 1.0.")
    parser.add_argument("--imgsz", type=int, help="YOLO input image size. Defaults to 640.")
    parser.add_argument("--legacy-opencv", action="store_true", help="Launch the old OpenCV keyboard-control UI.")
    return parser.parse_args()

def main():
    """Run the application"""
    try:
        args = parse_args()

        if not args.legacy_opencv:
            from ai_motion_app.qt_app import run_qt_app

            return run_qt_app(
                initial_video=args.video or args.input_video,
                camera_index=args.camera,
                model_name=args.model,
                model_device=args.device,
                detector_backend=args.backend,
                confidence_threshold=args.confidence,
                model_imgsz=args.imgsz,
            )

        from ai_motion_app.main_app import MotionDetectionApp

        app = MotionDetectionApp()
        if args.camera is not None:
            app.config.set('video_source', 'camera')
            app.config.set('camera_index', args.camera)
            app.camera.source_type = 'camera'
            app.camera.camera_index = args.camera
        selected_video = args.video or args.input_video
        if selected_video:
            video_path = str(Path(selected_video).expanduser())
            app.config.set('video_source', 'video')
            app.config.set('video_file_path', video_path)
            app.camera.source_type = 'video'
            app.camera.video_path = Path(video_path)
        if args.model:
            app.config.set('model_size', args.model)
            app.detector.model_name = args.model
        if args.device:
            app.config.set('model_device', args.device)
            app.detector.requested_device = args.device
            app.detector.device = args.device
        if args.confidence is not None:
            app.config.set('confidence_threshold', args.confidence)
            app.detector.confidence_threshold = args.confidence
        if args.imgsz is not None:
            app.config.set('model_imgsz', args.imgsz)
            app.detector.imgsz = args.imgsz
        app.run()
    except Exception as e:
        print(f"\n✗ Error running application: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
