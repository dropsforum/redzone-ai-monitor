import * as ort from 'onnxruntime-web';
import {
  calculateLetterbox,
  decodeYoloOutput,
  type LetterboxTransform,
} from './inference-core';

type WorkerGlobal = typeof self & { __logOnce_frameSize?: boolean };

let session: ort.InferenceSession | null = null;
const modelSize = 640;
const backend = 'onnx-wasm';

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
    self.postMessage({ type: 'LOADED', backend });
  } catch (e) {
    console.error('[Worker] Failed to load model:', e);
    self.postMessage({ type: 'ERROR', error: String(e) });
  }
}

// Run Inference
async function run(imageData: ImageData) {
  if (!session) return;

  const { width, height } = imageData;

  // Guard against zero-sized frames (can occur during camera init on mobile)
  if (!width || !height) {
    console.warn('[Worker] Skipping run due to zero-sized frame');
    self.postMessage({
      type: 'RESULT',
      result: {
        detections: [],
        backend,
        dropped: false,
        timings: { preprocessMs: 0, inferenceMs: 0, postprocessMs: 0, totalMs: 0 },
      },
    });
    return;
  }

  // Lightweight diagnostic to confirm incoming frame sizes on mobile
  const workerSelf = self as WorkerGlobal;
  if (workerSelf.__logOnce_frameSize !== true) {
    console.log(`[Worker] Frame ${width}x${height}`);
    workerSelf.__logOnce_frameSize = true;
  }

  try {
    const totalStartedAt = performance.now();
    const preprocessStartedAt = totalStartedAt;
    const transform = calculateLetterbox(width, height, modelSize);
    const letterboxed = drawLetterbox(imageData, transform);
    const float32Data = toNchw(letterboxed);
    const preprocessMs = performance.now() - preprocessStartedAt;
    
    const inputTensor = new ort.Tensor('float32', float32Data, [1, 3, modelSize, modelSize]);

    // 2. Inference
    const inferenceStartedAt = performance.now();
    const feeds: Record<string, ort.Tensor> = {};
    feeds[session.inputNames[0]] = inputTensor;
    const outputData = await session.run(feeds);
    const output = outputData[session.outputNames[0]];
    const inferenceMs = performance.now() - inferenceStartedAt;
    
    // 3. Postprocess
    const postprocessStartedAt = performance.now();
    const detections = decodeYoloOutput(
      output.data as Float32Array,
      output.dims,
      transform,
    );
    const postprocessMs = performance.now() - postprocessStartedAt;
    
    self.postMessage({
      type: 'RESULT',
      result: {
        detections,
        backend,
        dropped: false,
        timings: {
          preprocessMs,
          inferenceMs,
          postprocessMs,
          totalMs: performance.now() - totalStartedAt,
        },
      },
    });
  } catch (e) {
    console.error('[Worker] Detection error:', e);
    self.postMessage({ type: 'ERROR', error: String(e) });
  }
}

function drawLetterbox(imageData: ImageData, transform: LetterboxTransform): Uint8ClampedArray {
  if (typeof OffscreenCanvas !== 'undefined') {
    const source = new OffscreenCanvas(transform.inputWidth, transform.inputHeight);
    const sourceContext = source.getContext('2d');
    const target = new OffscreenCanvas(transform.modelSize, transform.modelSize);
    const targetContext = target.getContext('2d');
    if (sourceContext && targetContext) {
      sourceContext.putImageData(imageData, 0, 0);
      targetContext.fillStyle = 'rgb(114, 114, 114)';
      targetContext.fillRect(0, 0, transform.modelSize, transform.modelSize);
      targetContext.imageSmoothingEnabled = true;
      targetContext.imageSmoothingQuality = 'high';
      targetContext.drawImage(
        source,
        transform.padLeft,
        transform.padTop,
        transform.resizedWidth,
        transform.resizedHeight,
      );
      return targetContext.getImageData(0, 0, transform.modelSize, transform.modelSize).data;
    }
  }
  return bilinearLetterbox(imageData, transform);
}

function bilinearLetterbox(imageData: ImageData, transform: LetterboxTransform) {
  const output = new Uint8ClampedArray(transform.modelSize * transform.modelSize * 4);
  for (let index = 0; index < output.length; index += 4) {
    output[index] = 114;
    output[index + 1] = 114;
    output[index + 2] = 114;
    output[index + 3] = 255;
  }

  for (let targetY = 0; targetY < transform.resizedHeight; targetY++) {
    const sourceY = Math.max(0, Math.min(
      transform.inputHeight - 1,
      (targetY + 0.5) / transform.scaleY - 0.5,
    ));
    const y0 = Math.floor(sourceY);
    const y1 = Math.min(transform.inputHeight - 1, y0 + 1);
    const yWeight = sourceY - y0;

    for (let targetX = 0; targetX < transform.resizedWidth; targetX++) {
      const sourceX = Math.max(0, Math.min(
        transform.inputWidth - 1,
        (targetX + 0.5) / transform.scaleX - 0.5,
      ));
      const x0 = Math.floor(sourceX);
      const x1 = Math.min(transform.inputWidth - 1, x0 + 1);
      const xWeight = sourceX - x0;
      const targetIndex = (
        (targetY + transform.padTop) * transform.modelSize
        + targetX + transform.padLeft
      ) * 4;

      for (let channel = 0; channel < 3; channel++) {
        const top = imageData.data[(y0 * transform.inputWidth + x0) * 4 + channel] * (1 - xWeight)
          + imageData.data[(y0 * transform.inputWidth + x1) * 4 + channel] * xWeight;
        const bottom = imageData.data[(y1 * transform.inputWidth + x0) * 4 + channel] * (1 - xWeight)
          + imageData.data[(y1 * transform.inputWidth + x1) * 4 + channel] * xWeight;
        output[targetIndex + channel] = top * (1 - yWeight) + bottom * yWeight;
      }
    }
  }
  return output;
}

function toNchw(rgba: Uint8ClampedArray) {
  const planeSize = modelSize * modelSize;
  const float32Data = new Float32Array(3 * planeSize);
  for (let pixel = 0; pixel < planeSize; pixel++) {
    const source = pixel * 4;
    float32Data[pixel] = rgba[source] / 255;
    float32Data[pixel + planeSize] = rgba[source + 1] / 255;
    float32Data[pixel + planeSize * 2] = rgba[source + 2] / 255;
  }
  return float32Data;
}

self.onmessage = (e) => {
  if (e.data.type === 'INIT') init(e.data.modelPath);
  if (e.data.type === 'RUN') run(e.data.imageData);
};
