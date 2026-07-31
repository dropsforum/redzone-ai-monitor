"use client";

import React from 'react';
import type { Detection } from '../lib/yolo-detector';

type DisplayDetection = Detection & {
  trackId?: number;
  pendingEntry?: boolean;
  breachActive?: boolean;
};

interface DetectionOverlayProps {
  detections: DisplayDetection[];
  width: number;
  height: number;
}

const DetectionOverlay: React.FC<DetectionOverlayProps> = ({ detections, width, height }) => {
  if (width === 0 || height === 0) return null;

  return (
    <div className="absolute inset-0 pointer-events-none z-30">
      {detections.map((det, i) => {
        // Calculate percentages for responsive placement
        const left = (det.x1 / width) * 100;
        const top = (det.y1 / height) * 100;
        const boxWidth = ((det.x2 - det.x1) / width) * 100;
        const boxHeight = ((det.y2 - det.y1) / height) * 100;

        const tone = det.breachActive
          ? 'border-red-500 bg-red-500/10'
          : det.pendingEntry
            ? 'border-yellow-400 bg-yellow-400/10'
            : 'border-[#55799a] bg-[#55799a]/10';
        const labelTone = det.breachActive
          ? 'bg-red-600'
          : det.pendingEntry
            ? 'bg-yellow-500'
            : 'bg-[#55799a]';

        return (
          <div 
            key={det.trackId ?? i}
            className={`absolute border-2 rounded-sm transition-all duration-75 ${tone}`}
            style={{
              left: `${left}%`,
              top: `${top}%`,
              width: `${boxWidth}%`,
              height: `${boxHeight}%`,
            }}
          >
            <div className={`absolute -top-6 left-0 text-[10px] font-black text-white px-2 py-0.5 rounded-t-sm whitespace-nowrap uppercase tracking-tighter ${labelTone}`}>
              Person{det.trackId ? ` #${det.trackId}` : ''} {(det.confidence * 100).toFixed(0)}%
            </div>
            
            {/* Corner Accents */}
            <div className="absolute top-0 left-0 w-2 h-2 border-t-2 border-l-2 border-white/50" />
            <div className="absolute top-0 right-0 w-2 h-2 border-t-2 border-r-2 border-white/50" />
            <div className="absolute bottom-0 left-0 w-2 h-2 border-b-2 border-l-2 border-white/50" />
            <div className="absolute bottom-0 right-0 w-2 h-2 border-b-2 border-r-2 border-white/50" />
          </div>
        );
      })}
    </div>
  );
};

export default DetectionOverlay;
