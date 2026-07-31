import type { Detection } from './yolo-detector';

export interface LetterboxTransform {
  inputWidth: number;
  inputHeight: number;
  modelSize: number;
  scale: number;
  scaleX: number;
  scaleY: number;
  resizedWidth: number;
  resizedHeight: number;
  padLeft: number;
  padTop: number;
}

export interface DecodeOptions {
  confidenceThreshold?: number;
  iouThreshold?: number;
}

export function calculateLetterbox(
  inputWidth: number,
  inputHeight: number,
  modelSize: number,
): LetterboxTransform {
  if (inputWidth <= 0 || inputHeight <= 0 || modelSize <= 0) {
    throw new Error('Letterbox dimensions must be positive');
  }

  const scale = Math.min(modelSize / inputWidth, modelSize / inputHeight);
  const resizedWidth = Math.max(1, Math.round(inputWidth * scale));
  const resizedHeight = Math.max(1, Math.round(inputHeight * scale));

  return {
    inputWidth,
    inputHeight,
    modelSize,
    scale,
    scaleX: resizedWidth / inputWidth,
    scaleY: resizedHeight / inputHeight,
    resizedWidth,
    resizedHeight,
    padLeft: Math.floor((modelSize - resizedWidth) / 2),
    padTop: Math.floor((modelSize - resizedHeight) / 2),
  };
}

export function mapBoxFromModel(
  box: [number, number, number, number],
  transform: LetterboxTransform,
): [number, number, number, number] {
  const [rawX1, rawY1, rawX2, rawY2] = box;
  const modelScale = Math.max(Math.abs(rawX1), Math.abs(rawY1), Math.abs(rawX2), Math.abs(rawY2)) <= 1
    ? transform.modelSize
    : 1;
  const x1 = ((rawX1 * modelScale) - transform.padLeft) / transform.scaleX;
  const y1 = ((rawY1 * modelScale) - transform.padTop) / transform.scaleY;
  const x2 = ((rawX2 * modelScale) - transform.padLeft) / transform.scaleX;
  const y2 = ((rawY2 * modelScale) - transform.padTop) / transform.scaleY;

  return [
    clamp(Math.min(x1, x2), 0, transform.inputWidth),
    clamp(Math.min(y1, y2), 0, transform.inputHeight),
    clamp(Math.max(x1, x2), 0, transform.inputWidth),
    clamp(Math.max(y1, y2), 0, transform.inputHeight),
  ];
}

export function decodeYoloOutput(
  data: Float32Array,
  dims: readonly number[],
  transform: LetterboxTransform,
  options: DecodeOptions = {},
): Detection[] {
  const confidenceThreshold = options.confidenceThreshold ?? 0.35;
  const iouThreshold = options.iouThreshold ?? 0.45;
  const shape = dims.length === 3 && dims[0] === 1 ? dims.slice(1) : dims;
  if (shape.length !== 2) return [];

  const [first, second] = shape;
  const endToEnd = second === 6 && first <= 1000;
  if (endToEnd) {
    return readRows(data, first, second, false)
      .map(attrs => parseEndToEnd(attrs, transform, confidenceThreshold))
      .filter((detection): detection is Detection => detection !== null);
  }

  const firstLooksLikeAttributes = first >= 5 && first <= 512;
  const secondLooksLikeAttributes = second >= 5 && second <= 512;
  const attrMajor = firstLooksLikeAttributes !== secondLooksLikeAttributes
    ? firstLooksLikeAttributes
    : first <= second;
  const rows = attrMajor ? second : first;
  const attrs = attrMajor ? first : second;
  const decoded = readRows(data, rows, attrs, attrMajor)
    .map(values => parseTraditional(values, transform, confidenceThreshold))
    .filter((detection): detection is Detection => detection !== null);

  return nms(decoded, iouThreshold);
}

function readRows(
  data: Float32Array,
  rowCount: number,
  attrCount: number,
  attrMajor: boolean,
): number[][] {
  const rows: number[][] = [];
  for (let row = 0; row < rowCount; row++) {
    const attrs: number[] = [];
    for (let attr = 0; attr < attrCount; attr++) {
      attrs.push(attrMajor ? data[attr * rowCount + row] : data[row * attrCount + attr]);
    }
    rows.push(attrs);
  }
  return rows;
}

function parseEndToEnd(
  attrs: number[],
  transform: LetterboxTransform,
  confidenceThreshold: number,
): Detection | null {
  const [x1, y1, x2, y2, confidence, classId] = attrs;
  if (Math.round(classId) !== 0 || confidence <= confidenceThreshold) return null;
  const mapped = mapBoxFromModel([x1, y1, x2, y2], transform);
  if (mapped[2] <= mapped[0] || mapped[3] <= mapped[1]) return null;
  return toDetection(mapped, confidence);
}

function parseTraditional(
  attrs: number[],
  transform: LetterboxTransform,
  confidenceThreshold: number,
): Detection | null {
  if (attrs.length < 5) return null;
  const classScores = attrs.slice(4);
  let classId = 0;
  let confidence = classScores[0];
  for (let index = 1; index < classScores.length; index++) {
    if (classScores[index] > confidence) {
      confidence = classScores[index];
      classId = index;
    }
  }
  if (classId !== 0 || confidence <= confidenceThreshold) return null;

  const [cx, cy, width, height] = attrs;
  const mapped = mapBoxFromModel([
    cx - width / 2,
    cy - height / 2,
    cx + width / 2,
    cy + height / 2,
  ], transform);
  if (mapped[2] <= mapped[0] || mapped[3] <= mapped[1]) return null;
  return toDetection(mapped, confidence);
}

function toDetection(
  [x1, y1, x2, y2]: [number, number, number, number],
  confidence: number,
): Detection {
  return { x1, y1, x2, y2, confidence, classId: 0 };
}

function nms(boxes: Detection[], iouThreshold: number): Detection[] {
  const remaining = [...boxes].sort((a, b) => b.confidence - a.confidence);
  const selected: Detection[] = [];

  while (remaining.length > 0) {
    const next = remaining.shift();
    if (!next) break;
    selected.push(next);
    for (let index = remaining.length - 1; index >= 0; index--) {
      if (iou(next, remaining[index]) > iouThreshold) remaining.splice(index, 1);
    }
  }
  return selected;
}

function iou(a: Detection, b: Detection) {
  const x1 = Math.max(a.x1, b.x1);
  const y1 = Math.max(a.y1, b.y1);
  const x2 = Math.min(a.x2, b.x2);
  const y2 = Math.min(a.y2, b.y2);
  const intersection = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
  const areaA = Math.max(0, a.x2 - a.x1) * Math.max(0, a.y2 - a.y1);
  const areaB = Math.max(0, b.x2 - b.x1) * Math.max(0, b.y2 - b.y1);
  const union = areaA + areaB - intersection;
  return union > 0 ? intersection / union : 0;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}
