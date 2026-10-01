"use client";

import React, { useEffect, useRef, useCallback } from 'react';

export interface Point {
  x: number;
  y: number;
}

interface ZoneEditorProps {
  onZoneChange?: (points: Point[]) => void;
  width: number;
  height: number;
  isDrawing: boolean;
  initialPoints?: Point[];
}

const ZoneEditor: React.FC<ZoneEditorProps> = ({ 
  onZoneChange, 
  width, 
  height, 
  isDrawing,
  initialPoints = []
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const dragRef = useRef<{
    index: number;
    pointerId: number;
    offset: Point;
    points: Point[];
  } | null>(null);
  const points = initialPoints;

  const finishDrag = useCallback(() => {
    const canvas = canvasRef.current;
    const drag = dragRef.current;
    dragRef.current = null;
    if (canvas) {
      if (drag && canvas.hasPointerCapture(drag.pointerId)) {
        canvas.releasePointerCapture(drag.pointerId);
      }
      canvas.style.cursor = isDrawing ? 'crosshair' : '';
    }
  }, [isDrawing]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);
    if (points.length === 0) return;

    ctx.beginPath();
    ctx.moveTo(points[0].x * width, points[0].y * height);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x * width, points[i].y * height);
    }

    if (points.length > 2) {
      ctx.closePath();
    }
    if (!isDrawing && points.length > 2) {
      ctx.fillStyle = 'rgba(220, 38, 38, 0.3)'; // Red with alpha
      ctx.fill();
    }

    ctx.strokeStyle = '#dc2626'; // Red border
    ctx.lineWidth = 4;
    if (isDrawing) {
      ctx.setLineDash([5, 5]);
    } else {
      ctx.setLineDash([]);
    }
    ctx.stroke();

    if (isDrawing) {
      ctx.setLineDash([]);
      points.forEach((p) => {
        ctx.beginPath();
        ctx.arc(p.x * width, p.y * height, 8, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        ctx.strokeStyle = '#dc2626'; // Red handle border
        ctx.lineWidth = 2;
        ctx.stroke();
      });
    }
  }, [points, width, height, isDrawing]);

  useEffect(() => {
    draw();
  }, [draw]);

  useEffect(() => {
    if (!isDrawing || points.length !== dragRef.current?.points.length) {
      finishDrag();
    }
  }, [isDrawing, points.length, finishDrag]);

  const pointFromPointer = (e: React.PointerEvent<HTMLCanvasElement>): Point => {
    const rect = e.currentTarget.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) / rect.width,
      y: (e.clientY - rect.top) / rect.height,
    };
  };

  const nearestVertex = (e: React.PointerEvent<HTMLCanvasElement>): number => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pointer = pointFromPointer(e);
    let index = -1;
    let distance = e.pointerType === 'touch' ? 24 : 14;
    points.forEach((point, candidate) => {
      const nextDistance = Math.hypot(
        (point.x - pointer.x) * rect.width,
        (point.y - pointer.y) * rect.height,
      );
      if (nextDistance <= distance) {
        index = candidate;
        distance = nextDistance;
      }
    });
    return index;
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawing || e.button !== 0 || dragRef.current) return;
    e.preventDefault();
    const pointer = pointFromPointer(e);
    const index = nearestVertex(e);
    if (index >= 0) {
      dragRef.current = {
        index,
        pointerId: e.pointerId,
        offset: { x: points[index].x - pointer.x, y: points[index].y - pointer.y },
        points: [...points],
      };
      e.currentTarget.setPointerCapture(e.pointerId);
      e.currentTarget.style.cursor = 'grabbing';
    } else {
      onZoneChange?.([...points, pointer]);
    }
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const drag = dragRef.current;
    if (drag) {
      if (e.pointerId !== drag.pointerId) return;
      e.preventDefault();
      const pointer = pointFromPointer(e);
      drag.points[drag.index] = {
        x: Math.max(0, Math.min(1, pointer.x + drag.offset.x)),
        y: Math.max(0, Math.min(1, pointer.y + drag.offset.y)),
      };
      onZoneChange?.([...drag.points]);
    } else {
      e.currentTarget.style.cursor = nearestVertex(e) >= 0 ? 'grab' : 'crosshair';
    }
  };

  const clearZone = () => {
    finishDrag();
    onZoneChange?.([]);
  };

  const pointerClass = isDrawing ? 'pointer-events-auto cursor-crosshair' : 'pointer-events-none';

  return (
    <div className={"absolute inset-0 z-20 " + pointerClass}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="w-full h-full"
        aria-label="Zone editor"
        style={{ touchAction: isDrawing ? 'none' : 'auto' }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={(e) => { if (e.pointerId === dragRef.current?.pointerId) finishDrag(); }}
        onPointerCancel={(e) => { if (e.pointerId === dragRef.current?.pointerId) finishDrag(); }}
        onLostPointerCapture={finishDrag}
      />
      {isDrawing && points.length > 0 && (
        <div className="absolute top-4 right-4 pointer-events-auto">
          <button 
            onClick={(e) => { e.stopPropagation(); clearZone(); }}
            className="px-4 py-2 bg-slate-800 text-white text-[10px] font-black rounded-lg shadow-md hover:bg-slate-900 active:scale-95 transition-all uppercase tracking-widest"
          >
            Clear
          </button>
        </div>
      )}
    </div>
  );
};

export default ZoneEditor;
