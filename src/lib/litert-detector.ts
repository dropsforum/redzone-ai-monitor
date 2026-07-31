import type {
  BrowserInferenceBackend,
  InferenceResult,
} from './yolo-detector';
import type { YOLO as UltralyticsModel } from '@ultralytics/yolo';

const EMPTY_TIMINGS = {
  preprocessMs: 0,
  inferenceMs: 0,
  postprocessMs: 0,
  totalMs: 0,
};

export class LiteRtDetector implements BrowserInferenceBackend {
  private model: UltralyticsModel | null = null;
  private isProcessing = false;

  get backend() {
    return `litert-${this.model?.device ?? 'uninitialized'}`;
  }

  async init(modelPath: string) {
    const { YOLO } = await import('@ultralytics/yolo');
    this.model = await YOLO.load(modelPath, {
      device: 'auto',
      litertWasmUrl: '/litert/',
    });
    return true;
  }

  async detect(canvas: HTMLCanvasElement): Promise<InferenceResult> {
    if (!this.model) throw new Error('LiteRT detector is not initialized');
    if (this.isProcessing) {
      return {
        detections: [],
        backend: this.backend,
        timings: EMPTY_TIMINGS,
        dropped: true,
      };
    }

    this.isProcessing = true;
    const startedAt = performance.now();
    try {
      const results = await this.model.predict(canvas, {
        classes: [0],
        conf: 0.35,
        iou: 0.45,
      });
      return {
        detections: results.boxes.map(box => ({
          x1: box.x1,
          y1: box.y1,
          x2: box.x2,
          y2: box.y2,
          confidence: box.conf,
          classId: box.cls,
        })),
        backend: this.backend,
        timings: {
          preprocessMs: results.speed.preprocess,
          inferenceMs: results.speed.inference,
          postprocessMs: results.speed.postprocess,
          totalMs: performance.now() - startedAt,
        },
        dropped: false,
      };
    } finally {
      this.isProcessing = false;
    }
  }

  dispose() {
    this.model?.free();
    this.model = null;
    this.isProcessing = false;
  }
}
