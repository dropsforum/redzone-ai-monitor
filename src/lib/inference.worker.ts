import * as ort from 'onnxruntime-web';

// Simple types for the worker
interface Detection {
  x1: number; y1: number; x2: number; y2: number;
  confidence: number; classId: number;
}

let session: ort.InferenceSession | null = null;
const modelSize = 640;
const confidenceThreshold = 0.35; // Standard threshold
const iouThreshold = 0.45;

// Initialize ONNX
async function init(modelPath: string) {
  try {
    // Tell ONNX where to find WASM files from within the worker
    // Using an absolute path to the public wasm folder
    ort.env.wasm.wasmPaths = '/wasm/';

    session = await ort.InferenceSession.create(modelPath, {
      executionProviders: ['wasm'],
      graphOptimizationLevel: 'all',
    });
    self.postMessage({ type: 'LOADED' });
  } catch (e) {
    console.error('[Worker] Failed to load model:', e);
    self.postMessage({ type: 'ERROR', error: String(e) });
  }
}

// Run Inference
async function run(imageData: ImageData) {
  if (!session) return;

  const { width, height, data } = imageData;

  // Guard against zero-sized frames (can occur during camera init on mobile)
  if (!width || !height) {
    console.warn('[Worker] Skipping run due to zero-sized frame');
    self.postMessage({ type: 'RESULT', detections: [] });
    return;
  }

  // Lightweight diagnostic to confirm incoming frame sizes on mobile
  if ((self as any).__logOnce_frameSize !== true) {
    console.log(`[Worker] Frame ${width}x${height}`);
    (self as any).__logOnce_frameSize = true;
  }

  try {
    // 1. Preprocess (Normalized Float32 NCHW)
    const float32Data = new Float32Array(3 * modelSize * modelSize);
    
    // Use scale factors instead of integer stride so small frames (<640px) still map correctly
    const scaleX = width / modelSize;
    const scaleY = height / modelSize;

    for (let y = 0; y < modelSize; y++) {
      const srcY = Math.min(height - 1, Math.floor((y + 0.5) * scaleY));
      for (let x = 0; x < modelSize; x++) {
        const srcX = Math.min(width - 1, Math.floor((x + 0.5) * scaleX));
        const sourceIdx = (srcY * width + srcX) * 4;

        const i = (y * modelSize + x);
        float32Data[i] = data[sourceIdx] / 255.0; // R
        float32Data[i + modelSize * modelSize] = data[sourceIdx + 1] / 255.0; // G
        float32Data[i + 2 * modelSize * modelSize] = data[sourceIdx + 2] / 255.0; // B
      }
    }
    
    const inputTensor = new ort.Tensor('float32', float32Data, [1, 3, modelSize, modelSize]);

    // 2. Inference
    const feeds: any = {};
    feeds[session.inputNames[0]] = inputTensor;
    const outputData = await session.run(feeds);
    const output = outputData[session.outputNames[0]];
    
    // 3. Postprocess
    const detections = postprocess(output, width, height);
    
    self.postMessage({ type: 'RESULT', detections });
  } catch (e) {
    console.error('[Worker] Detection error:', e);
    self.postMessage({ type: 'ERROR', error: String(e) });
  }
}

function postprocess(output: ort.Tensor, origWidth: number, origHeight: number): Detection[] {
  const data = output.data as Float32Array;
  const dims = output.dims; // [1, 84, 8400]
  const numRows = dims[1]; // 84
  const numCols = dims[2]; // 8400

  const boxes: Detection[] = [];

  for (let i = 0; i < numCols; i++) {
    // YOLOv11 structure: first 4 are box (cx, cy, w, h), rest are classes
    // Class 0 is 'person'
    const personScore = data[4 * numCols + i];

    if (personScore > confidenceThreshold) {
      const cx = data[0 * numCols + i];
      const cy = data[1 * numCols + i];
      const w = data[2 * numCols + i];
      const h = data[3 * numCols + i];

      // Convert to actual pixel coordinates on the original frame
      const x1 = ((cx - w / 2) / modelSize) * origWidth;
      const y1 = ((cy - h / 2) / modelSize) * origHeight;
      const x2 = ((cx + w / 2) / modelSize) * origWidth;
      const y2 = ((cy + h / 2) / modelSize) * origHeight;

      boxes.push({ x1, y1, x2, y2, confidence: personScore, classId: 0 });
    }
  }

  return nms(boxes);
}

function nms(boxes: Detection[]): Detection[] {
  const sorted = [...boxes].sort((a, b) => b.confidence - a.confidence);
  const selected: Detection[] = [];
  const active = new Array(sorted.length).fill(true);

  for (let i = 0; i < sorted.length; i++) {
    if (!active[i]) continue;
    const boxA = sorted[i];
    selected.push(boxA);
    for (let j = i + 1; j < sorted.length; j++) {
      if (!active[j]) continue;
      if (iou(boxA, sorted[j]) > iouThreshold) active[j] = false;
    }
  }
  return selected;
}

function iou(boxA: Detection, boxB: Detection): number {
  const xA = Math.max(boxA.x1, boxB.x1);
  const yA = Math.max(boxA.y1, boxB.y1);
  const xB = Math.min(boxA.x2, boxB.x2);
  const yB = Math.min(boxA.y2, boxB.y2);
  const intersection = Math.max(0, xB - xA) * Math.max(0, yB - yA);
  const areaA = (boxA.x2 - boxA.x1) * (boxA.y2 - boxA.y1);
  const areaB = (boxB.x2 - boxB.x1) * (boxB.y2 - boxB.y1);
  return intersection / (areaA + areaB - intersection);
}

self.onmessage = (e) => {
  if (e.data.type === 'INIT') init(e.data.modelPath);
  if (e.data.type === 'RUN') run(e.data.imageData);
};
