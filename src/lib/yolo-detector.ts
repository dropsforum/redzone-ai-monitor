import * as ort from 'onnxruntime-web';

export interface Detection {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  confidence: number;
  classId: number;
}

export interface InferenceTimings {
  preprocessMs: number;
  inferenceMs: number;
  postprocessMs: number;
  totalMs: number;
}

export interface InferenceResult {
  detections: Detection[];
  backend: string;
  timings: InferenceTimings;
  dropped: boolean;
}

export interface BrowserInferenceBackend {
  readonly backend: string;
  init(modelPath: string): Promise<boolean>;
  detect(canvas: HTMLCanvasElement): Promise<InferenceResult>;
  dispose(): void;
}

const EMPTY_TIMINGS: InferenceTimings = {
  preprocessMs: 0,
  inferenceMs: 0,
  postprocessMs: 0,
  totalMs: 0,
};

export class YoloDetector implements BrowserInferenceBackend {
  readonly backend = 'onnx-wasm';
  private worker: Worker | null = null;
  private isProcessing = false;
  private resolveInit: ((value: boolean) => void) | null = null;
  private rejectInit: ((reason?: unknown) => void) | null = null;
  private resolveDetect: ((value: InferenceResult) => void) | null = null;
  private rejectDetect: ((reason?: unknown) => void) | null = null;

  async init(modelPath: string) {
    // Configure WASM paths for the main thread as well (sometimes needed for initialization)
    ort.env.wasm.wasmPaths = '/wasm/';
    
    return new Promise<boolean>((resolve, reject) => {
      try {
        this.resolveInit = resolve;
        this.rejectInit = reject;
        
        // Initialize Worker
        this.worker = new Worker(new URL('./inference.worker.ts', import.meta.url));
        
        this.worker.onmessage = (e) => {
          const { type, result, error } = e.data;
          
          if (type === 'LOADED') {
            console.log('[YOLO] ✓ Worker loaded and model initialized.');
            this.resolveInit?.(true);
            this.resolveInit = null;
            this.rejectInit = null;
          } else if (type === 'RESULT') {
            this.resolveDetect?.(result);
            this.resolveDetect = null;
            this.rejectDetect = null;
            this.isProcessing = false;
          } else if (type === 'ERROR') {
            console.error('[YOLO] ✗ Worker error:', error);
            const workerError = new Error(error);
            this.rejectInit?.(workerError);
            this.rejectDetect?.(workerError);
            this.resolveInit = null;
            this.rejectInit = null;
            this.resolveDetect = null;
            this.rejectDetect = null;
            this.isProcessing = false;
          }
        };

        this.worker.postMessage({ type: 'INIT', modelPath });
      } catch (e) {
        console.error('[YOLO] ✗ Failed to initialize worker:', e);
        reject(e);
      }
    });
  }

  async detect(canvas: HTMLCanvasElement): Promise<InferenceResult> {
    if (!this.worker) throw new Error('YOLO detector is not initialized');
    if (this.isProcessing) {
      return {
        detections: [],
        backend: this.backend,
        timings: EMPTY_TIMINGS,
        dropped: true,
      };
    }
    
    this.isProcessing = true;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      this.isProcessing = false;
      throw new Error('Unable to read the video frame canvas');
    }

    // Capture image data to send to worker
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

    return new Promise<InferenceResult>((resolve, reject) => {
      this.resolveDetect = resolve;
      this.rejectDetect = reject;
      // Transfer the buffer for high performance
      this.worker?.postMessage({ 
        type: 'RUN', 
        imageData 
      }, [imageData.data.buffer]);
    });
  }

  dispose() {
    this.worker?.terminate();
    this.worker = null;
    this.isProcessing = false;
    this.resolveDetect = null;
    this.rejectDetect = null;
  }
}
