# redzone-web-app Integration Package

This package contains the Next.js browser-based YOLO detection module for integration into `dropsforum.org`.

## What's included

- **AI Engine**: Client-side YOLOv11 (ONNX Runtime Web)
- **UI Components**: Webcam capture, Touch-friendly Zone Editor, Detection Overlay
- **Logic**: Zone intrusion detection, Alert system
- **Performance**: Optimized for Desktop (10 FPS) and Mobile (3 FPS)

## Local Development

To run this app locally for testing:

1. **Install dependencies**: `npm install`
2. **Launch server**: `npm run dev`
3. **Open browser**: Go to `http://localhost:3000` (or `http://localhost:3001` if 3000 is occupied).

## How to integrate into dropsforum.org

### 1. Copy Files
Copy these directories into your `dropsforum.org` project:
- `src/components/*` -> `components/`
- `src/lib/*` -> `lib/`
- `public/models/yolo11n.onnx` -> `public/models/`

### 2. Install Dependencies
Run this in your website project:
```bash
npm install onnxruntime-web lucide-react clsx tailwind-merge copy-webpack-plugin
```

### 3. Update next.config.ts
Add the WASM copy plugin to your `next.config.ts`:
```typescript
import CopyPlugin from "copy-webpack-plugin";

// ... inside nextConfig.webpack
config.plugins.push(
  new CopyPlugin({
    patterns: [
      {
        from: "node_modules/onnxruntime-web/dist/*.wasm",
        to: "static/chunks/[name][ext]",
      },
    ],
  })
);
```

### 4. Use the Monitoring Page
Copy `src/app/page.tsx` (or its contents) to your desired route (e.g., `app/redzone/page.tsx`).

## Note on Mobile Performance
The app automatically detects mobile devices and reduces inference frequency and resolution to preserve battery and performance.
