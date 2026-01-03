import * as ort from 'onnxruntime-web';

export interface Detection {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  confidence: number;
  classId: number;
}

export class YoloDetector {
  private worker: Worker | null = null;
  private modelSize = 640;
  private isProcessing = false;
  private resolveInit: ((value: boolean) => void) | null = null;
  private resolveDetect: ((value: Detection[]) => void) | null = null;

  async init(modelPath: string) {
    // Configure WASM paths for the main thread as well (sometimes needed for initialization)
    ort.env.wasm.wasmPaths = '/wasm/';
    
    return new Promise<boolean>((resolve, reject) => {
      try {
        this.resolveInit = resolve;
        
        // Initialize Worker
        this.worker = new Worker(new URL('./inference.worker.ts', import.meta.url));
        
        this.worker.onmessage = (e) => {
          const { type, detections, error } = e.data;
          
          if (type === 'LOADED') {
            console.log('[YOLO] ✓ Worker loaded and model initialized.');
            this.resolveInit?.(true);
          } else if (type === 'RESULT') {
            this.resolveDetect?.(detections);
            this.isProcessing = false;
          } else if (type === 'ERROR') {
            console.error('[YOLO] ✗ Worker error:', error);
            reject(error);
          }
        };

        this.worker.postMessage({ type: 'INIT', modelPath });
      } catch (e) {
        console.error('[YOLO] ✗ Failed to initialize worker:', e);
        reject(e);
      }
    });
  }

  async detect(canvas: HTMLCanvasElement): Promise<Detection[]> {
    if (!this.worker || this.isProcessing) return [];
    
    this.isProcessing = true;
    const ctx = canvas.getContext('2d');
    if (!ctx) return [];

    // Capture image data to send to worker
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

    return new Promise<Detection[]>((resolve) => {
      this.resolveDetect = resolve;
      // Transfer the buffer for high performance
      this.worker?.postMessage({ 
        type: 'RUN', 
        imageData 
      }, [imageData.data.buffer]);
    });
  }
}
