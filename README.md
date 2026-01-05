# DROPS Red Zone Monitoring Web App

This is a Next.js-based Proof of Concept (POC) for the DROPS Red Zone Monitoring system. It uses browser-side AI (YOLOv11) to detect people entering user-defined exclusion zones.

## 🚀 Getting Started

### Prerequisites

- Node.js (Latest LTS recommended)
- npm (comes with Node.js)

### Local Setup

1.  **Install dependencies**:
    ```bash
    npm install
    ```

2.  **Start the development server**:
    ```bash
    npm run dev
    ```

3.  **Access the app**:
    Open [http://localhost:3000](http://localhost:3000) in your browser.
    *Note: If port 3000 is in use, Next.js will automatically try 3001, 3002, etc.*

## 🌐 Deployment (Vercel)

This project is optimized for deployment on Vercel.

**Note on Build**: Due to custom Webpack configurations required for ONNX Runtime Web, you must ensure the build command uses the `--webpack` flag:
- **Build Command**: `npm run build` (which is mapped to `next build --webpack` in `package.json`)
- **Framework Preset**: Next.js
- **Node.js Version**: 20.x or 22.x

## 📦 Features

- **Real-time AI Detection**: Runs YOLOv11 directly in your browser using ONNX Runtime Web.
- **Custom Zones**: Draw and edit monitoring zones directly on the live camera feed.
- **Visual Alerts**: On-screen indicators and sound alerts when someone enters a "Red Zone".
- **Privacy First**: All processing happens locally on your device. No video data is sent to any server.

## 🛠 Project Structure

- `src/components`: UI components (Webcam, Zone Editor, Overlays).
- `src/lib`: Core logic (YOLO detector, zone checking, alert management).
- `public/models`: Pre-trained YOLOv11 ONNX model.
- `public/wasm`: WebAssembly files for ONNX Runtime.

## 📄 Integration & Documentation

For instructions on integrating this module into the `dropsforum.org` website, see [PACKAGE_README.md](./PACKAGE_README.md).

---
*DROPS FORUM Red Zone Monitoring POC*
