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
  const points = initialPoints;

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

    if (!isDrawing && points.length > 2) {
      ctx.closePath();
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
      points.forEach((p) => {
        ctx.beginPath();
        ctx.arc(p.x * width, p.y * height, 6, 0, Math.PI * 2);
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

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;
    const y = (e.clientY - rect.top) / rect.height;
    const newPoints = [...points, { x, y }];
    onZoneChange?.(newPoints);
  };

  const clearZone = () => {
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
        onClick={handleClick}
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
