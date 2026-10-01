// @vitest-environment happy-dom

import React, { act, useState } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import ZoneEditor, { type Point } from './ZoneEditor';

const context = {
  arc: vi.fn(),
  beginPath: vi.fn(),
  clearRect: vi.fn(),
  closePath: vi.fn(),
  fill: vi.fn(),
  lineTo: vi.fn(),
  moveTo: vi.fn(),
  setLineDash: vi.fn(),
  stroke: vi.fn(),
  fillStyle: '',
  lineWidth: 0,
  strokeStyle: '',
};

let root: Root | undefined;
let container: HTMLDivElement | undefined;

function renderEditor(points: Point[], isDrawing = true) {
  container = document.createElement('div');
  document.body.append(container);
  root = createRoot(container);

  function Editor() {
    const [zone, setZone] = useState(points);
    return React.createElement(ZoneEditor, {
      width: 100,
      height: 100,
      isDrawing,
      initialPoints: zone,
      onZoneChange: setZone,
    });
  }

  act(() => root?.render(React.createElement(Editor)));
  const canvas = container.querySelector('canvas') as HTMLCanvasElement;
  vi.spyOn(canvas, 'getBoundingClientRect').mockReturnValue({
    bottom: 120,
    height: 100,
    left: 10,
    right: 110,
    top: 20,
    width: 100,
    x: 10,
    y: 20,
    toJSON: () => ({}),
  });
  return canvas;
}

function pointer(canvas: HTMLCanvasElement, type: string, x: number, y: number, options: PointerEventInit = {}) {
  act(() => canvas.dispatchEvent(new PointerEvent(type, {
    bubbles: true,
    button: 0,
    clientX: x,
    clientY: y,
    pointerId: 1,
    pointerType: 'mouse',
    ...options,
  })));
}

beforeEach(() => {
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(context as unknown as CanvasRenderingContext2D);
});

afterEach(() => {
  root?.unmount();
  container?.remove();
  root = undefined;
  container = undefined;
  vi.restoreAllMocks();
  context.arc.mockClear();
  context.beginPath.mockClear();
  context.clearRect.mockClear();
  context.closePath.mockClear();
  context.fill.mockClear();
  context.lineTo.mockClear();
  context.moveTo.mockClear();
  context.setLineDash.mockClear();
  context.stroke.mockClear();
});

describe('ZoneEditor', () => {
  it('creates normalized points on canvas clicks', () => {
    const canvas = renderEditor([]);

    pointer(canvas, 'pointerdown', 35, 70);

    expect(context.moveTo).toHaveBeenCalledWith(25, 50);
  });

  it('drags a corner using its grab offset, clamps it to the canvas, and releases capture', () => {
    const canvas = renderEditor([{ x: 0.5, y: 0.5 }]);
    const capture = vi.spyOn(canvas, 'setPointerCapture');
    const release = vi.spyOn(canvas, 'releasePointerCapture');
    vi.spyOn(canvas, 'hasPointerCapture').mockReturnValue(true);

    pointer(canvas, 'pointerdown', 58, 70);
    pointer(canvas, 'pointermove', 68, 70);
    pointer(canvas, 'pointermove', 250, -30);
    pointer(canvas, 'pointerup', 250, -30);

    expect(capture).toHaveBeenCalledWith(1);
    expect(context.arc).toHaveBeenCalledTimes(3);
    expect(context.arc).toHaveBeenCalledWith(60, 50, 8, 0, Math.PI * 2);
    expect(context.arc).toHaveBeenCalledWith(100, 0, 8, 0, Math.PI * 2);
    expect(release).toHaveBeenCalledWith(1);
  });

  it('uses the larger touch target to drag without creating another point', () => {
    const canvas = renderEditor([{ x: 0.5, y: 0.5 }]);
    const capture = vi.spyOn(canvas, 'setPointerCapture');

    pointer(canvas, 'pointerdown', 72, 70, { pointerType: 'touch' });

    expect(capture).toHaveBeenCalledWith(1);
    expect(context.arc).toHaveBeenCalledTimes(1);
  });

  it('is inert outside editing mode and clears editable zones', () => {
    const inactive = renderEditor([{ x: 0.5, y: 0.5 }], false);
    pointer(inactive, 'pointerdown', 40, 60);
    expect(context.arc).not.toHaveBeenCalled();

    root?.unmount();
    container?.remove();
    root = undefined;
    container = undefined;
    context.arc.mockClear();

    const active = renderEditor([{ x: 0.5, y: 0.5 }]);
    act(() => (container?.querySelector('button') as HTMLButtonElement).click());

    expect(active.parentElement?.querySelector('button')).toBeNull();
  });

  it('fills saved polygons with translucent red', () => {
    renderEditor([
      { x: 0.1, y: 0.1 },
      { x: 0.9, y: 0.1 },
      { x: 0.5, y: 0.9 },
    ], false);

    expect(context.fillStyle).toBe('rgba(220, 38, 38, 0.3)');
    expect(context.fill).toHaveBeenCalled();
  });
});
