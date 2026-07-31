import { describe, expect, it } from 'vitest';

import {
  calculateLetterbox,
  decodeYoloOutput,
  mapBoxFromModel,
} from './inference-core';

describe('browser inference geometry', () => {
  it('letterboxes a widescreen frame without stretching it', () => {
    expect(calculateLetterbox(1280, 720, 640)).toEqual({
      inputWidth: 1280,
      inputHeight: 720,
      modelSize: 640,
      scale: 0.5,
      scaleX: 0.5,
      scaleY: 0.5,
      resizedWidth: 640,
      resizedHeight: 360,
      padLeft: 0,
      padTop: 140,
    });
  });

  it('maps model-space boxes back through the letterbox', () => {
    const transform = calculateLetterbox(1280, 720, 640);
    expect(mapBoxFromModel([100, 190, 300, 390], transform)).toEqual([
      200,
      100,
      600,
      500,
    ]);
  });

  it('restores odd-size frames to within one pixel after rounded resizing', () => {
    const transform = calculateLetterbox(1919, 1079, 640);
    const sourceBox: [number, number, number, number] = [137, 91, 1733, 997];
    const modelBox: [number, number, number, number] = [
      sourceBox[0] * transform.scaleX + transform.padLeft,
      sourceBox[1] * transform.scaleY + transform.padTop,
      sourceBox[2] * transform.scaleX + transform.padLeft,
      sourceBox[3] * transform.scaleY + transform.padTop,
    ];

    const restored = mapBoxFromModel(modelBox, transform);
    restored.forEach((value, index) => {
      expect(Math.abs(value - sourceBox[index])).toBeLessThanOrEqual(1);
    });
  });

  it('does not apply NMS to YOLO26 end-to-end output', () => {
    const transform = calculateLetterbox(640, 640, 640);
    const output = new Float32Array([
      100, 100, 300, 500, 0.9, 0,
      110, 110, 310, 510, 0.8, 0,
    ]);

    const detections = decodeYoloOutput(output, [1, 2, 6], transform);

    expect(detections).toHaveLength(2);
  });

  it('retains NMS for traditional anchor output', () => {
    const transform = calculateLetterbox(640, 640, 640);
    const output = new Float32Array([
      200, 210,
      300, 310,
      200, 200,
      400, 400,
      0.9, 0.8,
    ]);

    const detections = decodeYoloOutput(output, [1, 5, 2], transform);

    expect(detections).toHaveLength(1);
    expect(detections[0].confidence).toBeCloseTo(0.9);
  });
});
