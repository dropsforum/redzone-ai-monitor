# Web Release - 2026-10-01

## Changes

- Edit existing zone corners with mouse or touch; dragging preserves the grab
  offset, captures the pointer, and clamps points to the video boundaries.
- Preserve the transparent red fill for saved zones.
- Show camera connection progress and a retry action after a 12-second startup
  timeout, rather than leaving an indefinitely blank panel.
- Cancel obsolete camera attempts without stopping a newer camera stream.
  Release streams arriving after cancellation or timeout.
- Keep video/canvas elements mounted during errors so retry can attach to them.
- Stop monitoring when the camera disconnects. Clear stale detections, FPS, and
  traffic-light state when monitoring stops.
- Prevent old recorded frames from being accepted as a newly selected camera.
- Device refresh only enumerates cameras; it does not open a second camera.
- Update Next.js and its lint configuration to 16.3.8, sharp to 0.35.4, and
  Vitest to 4.1.11. Refresh compatible transitive security fixes.

The browser still uses YOLO26n detection with ONNX/WASM. This release does not
port the Mac-only segmentation model or change model licensing/provisioning.
No model weights are added to the public Git repository. The private deployment
continues to provide its existing ONNX model.

## Verification

- Clean dependency install, 26 unit/component tests, lint, and production build.
- Dependency audit: zero reported vulnerabilities, including development tools.
- Real-browser test with a generated local MP4: choose file, drag a corner, save
  translucent red polygon, start monitoring, normal-speed playback, looping,
  inference, recording, and stop/pause.
- Regression tests cover hung requests, late rejection/resolution, stream
  cleanup, retry, disconnection, stale-file readiness, and callback changes.
- Independent scoped camera review; its stale-file readiness finding was fixed
  and locked down with a failing-then-passing regression test.

Actual camera availability and browser/OS permissions still depend on the user's
device. A camera timeout is now actionable; it is not evidence that the physical
camera is healthy.
