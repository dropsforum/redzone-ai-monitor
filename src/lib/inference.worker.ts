import * as ort from 'onnxruntime-web';

// Simple types for the worker
interface Detection {
  x1: number; y1: number; x2: number; y2: number;
  confidence: number; classId: number;
}

type WorkerGlobal = typeof self & { __logOnce_frameSize?: boolean };

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
  const workerSelf = self as WorkerGlobal;
  if (workerSelf.__logOnce_frameSize !== true) {
    console.log(`[Worker] Frame ${width}x${height}`);
    workerSelf.__logOnce_frameSize = true;
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
    const feeds: Record<string, ort.Tensor> = {};
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
  const dims = output.dims;

  if (dims.length === 3) {
    const [, first, second] = dims;
    const attrMajor = first <= second;
    return nms(readYoloRows(data, attrMajor ? second : first, attrMajor ? first : second, attrMajor, origWidth, origHeight));
  }

  if (dims.length === 2) {
    return nms(readYoloRows(data, dims[0], dims[1], false, origWidth, origHeight));
  }

  console.warn('[Worker] Unsupported output dimensions:', dims);
  return [];
}

function readYoloRows(
  data: Float32Array,
  rowCount: number,
  attrCount: number,
  attrMajor: boolean,
  origWidth: number,
  origHeight: number,
): Detection[] {
  const boxes: Detection[] = [];

  for (let i = 0; i < rowCount; i++) {
    const attrs = Array.from({ length: attrCount }, (_, attrIndex) => (
      attrMajor ? data[attrIndex * rowCount + i] : data[i * attrCount + attrIndex]
    ));
    const detection = parseDetection(attrs, origWidth, origHeight);
    if (detection) boxes.push(detection);
  }

  return boxes;
}

function parseDetection(attrs: number[], origWidth: number, origHeight: number): Detection | null {
  if (attrs.length < 5) return null;

  if (attrs.length === 6 && Number.isInteger(Math.round(attrs[5]))) {
    const [x1, y1, x2, y2, score, classId] = attrs;
    if (Math.round(classId) !== 0 || score <= confidenceThreshold) return null;
    return scaleBox({ x1, y1, x2, y2, confidence: score, classId: 0 }, origWidth, origHeight, true);
  }

  const classScores = attrs.slice(4);
  if (!classScores.length) return null;

  let classId = 0;
  let confidence = classScores[0];
  for (let i = 1; i < classScores.length; i++) {
    if (classScores[i] > confidence) {
      confidence = classScores[i];
      classId = i;
    }
  }

  if (classId !== 0 || confidence <= confidenceThreshold) return null;

  const [cx, cy, w, h] = attrs;
  return scaleBox({
    x1: cx - w / 2,
    y1: cy - h / 2,
    x2: cx + w / 2,
    y2: cy + h / 2,
    confidence,
    classId,
  }, origWidth, origHeight, false);
}

function scaleBox(box: Detection, origWidth: number, origHeight: number, xyxyOutput: boolean): Detection {
  const maxCoord = Math.max(Math.abs(box.x1), Math.abs(box.y1), Math.abs(box.x2), Math.abs(box.y2));
  const scaleX = maxCoord <= 1 ? origWidth : origWidth / modelSize;
  const scaleY = maxCoord <= 1 ? origHeight : origHeight / modelSize;

  const scaled = {
    ...box,
    x1: box.x1 * scaleX,
    y1: box.y1 * scaleY,
    x2: box.x2 * scaleX,
    y2: box.y2 * scaleY,
  };

  if (!xyxyOutput || scaled.x2 >= scaled.x1) return scaled;

  return {
    ...scaled,
    x1: scaled.x2,
    x2: scaled.x1,
    y1: Math.min(scaled.y1, scaled.y2),
    y2: Math.max(scaled.y1, scaled.y2),
  };
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
