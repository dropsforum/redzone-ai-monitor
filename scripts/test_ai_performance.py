#!/usr/bin/env python3
"""
Quick benchmark to test AI model performance on this Mac
This will test YOLO inference speed without actually needing a camera
"""

import time
import numpy as np

print("=" * 60)
print("AI Model Performance Test")
print("=" * 60)
print()

# Test 1: Check if ultralytics (YOLO) is available
print("Test 1: Checking for YOLO (ultralytics)...")
try:
    from ultralytics import YOLO
    print("✓ Ultralytics YOLO is installed")
    
    # Load the smallest model for testing
    print("\nLoading YOLOv8 nano model...")
    model = YOLO('yolov8n.pt')  # Will auto-download if not present
    print("✓ Model loaded successfully")
    
    # Create a dummy image (simulating camera frame)
    print("\nRunning benchmark with 640x480 resolution...")
    dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    # Warm-up run
    _ = model(dummy_image, verbose=False)
    
    # Benchmark
    num_frames = 30
    start_time = time.time()
    for i in range(num_frames):
        results = model(dummy_image, verbose=False)
    end_time = time.time()
    
    elapsed = end_time - start_time
    fps = num_frames / elapsed
    
    print(f"\n{'='*60}")
    print(f"BENCHMARK RESULTS")
    print(f"{'='*60}")
    print(f"Processed {num_frames} frames in {elapsed:.2f} seconds")
    print(f"Average FPS: {fps:.1f}")
    print(f"Average latency: {(elapsed/num_frames)*1000:.1f}ms per frame")
    print()
    
    if fps >= 30:
        print("✅ EXCELLENT - Your Mac can easily handle real-time video!")
    elif fps >= 15:
        print("✅ GOOD - Your Mac can handle real-time detection")
    else:
        print("⚠️  Your Mac might struggle with real-time video")
    
    print()
    print("Model size: ~6MB (YOLOv8 nano)")
    print("Can detect: 80 object types (person, car, dog, etc.)")
    print()
    
except ImportError:
    print("✗ Ultralytics YOLO not installed")
    print("\nTo install, run:")
    print("  pip install ultralytics")
    print()

# Test 2: Check for CoreML
print("\n" + "="*60)
print("Test 2: Checking for CoreML support...")
try:
    import coremltools
    print("✓ CoreML tools installed")
    print("✓ Your M4 has Neural Engine - CoreML will be VERY fast")
except ImportError:
    print("✗ CoreML tools not installed")
    print("\nTo install, run:")
    print("  pip install coremltools")

# Test 3: Check OpenCV
print("\n" + "="*60)
print("Test 3: Checking for OpenCV...")
try:
    import cv2
    print("✓ OpenCV is installed")
    print(f"  Version: {cv2.__version__}")
    
    # Check if we can access camera
    print("\nTesting camera access...")
    cap = cv2.VideoCapture(0)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✓ Camera accessible")
            print(f"  Resolution: {frame.shape[1]}x{frame.shape[0]}")
        cap.release()
    else:
        print("✗ Could not access camera")
        print("  (This is normal if camera is in use)")
    
except ImportError:
    print("✗ OpenCV not installed")
    print("\nTo install, run:")
    print("  pip install opencv-python")

print("\n" + "="*60)
print("System Information")
print("="*60)
import platform
print(f"OS: {platform.system()} {platform.release()}")
print(f"Architecture: {platform.machine()}")
print(f"Python: {platform.python_version()}")

print("\n" + "="*60)
print("\nRecommendation:")
print("Based on your M4 chip, I recommend YOLOv8 for:")
print("  • Excellent performance (60+ FPS expected)")
print("  • Easy to use and customize")
print("  • Works completely offline")
print("  • Detects people, cars, animals, and 77 other objects")
print("="*60)



