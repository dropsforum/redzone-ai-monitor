"use client";

import React from 'react';

export type TrafficLightState = 'red' | 'yellow' | 'green';

interface TrafficLightProps {
  state: TrafficLightState;
}

export default function TrafficLight({ state }: TrafficLightProps) {
  const lights = [
    { color: 'red', active: state === 'red' },
    { color: 'yellow', active: state === 'yellow' },
    { color: 'green', active: state === 'green' },
  ];

  const getLightClasses = (color: string, active: boolean) => {
    if (active) {
      switch (color) {
        case 'red':
          return 'bg-red-500 border-red-400 shadow-lg shadow-red-500/50';
        case 'yellow':
          return 'bg-yellow-500 border-yellow-400 shadow-lg shadow-yellow-500/50';
        case 'green':
          return 'bg-green-500 border-green-400 shadow-lg shadow-green-500/50';
        default:
          return 'bg-slate-500 border-slate-400';
      }
    } else {
      switch (color) {
        case 'red':
          return 'bg-red-500/30 border-slate-600/50';
        case 'yellow':
          return 'bg-yellow-500/30 border-slate-600/50';
        case 'green':
          return 'bg-green-500/30 border-slate-600/50';
        default:
          return 'bg-slate-500/30 border-slate-600/50';
      }
    }
  };

  return (
    <div className="absolute bottom-4 right-4 z-50 flex flex-col items-center gap-2.5 bg-white/90 backdrop-blur-sm rounded-xl p-2.5 border border-slate-200 shadow-sm">
      {lights.map((light) => (
        <div
          key={light.color}
          className={`w-3.5 h-3.5 rounded-full border-2 transition-all duration-200 ${getLightClasses(light.color, light.active)}`}
        />
      ))}
    </div>
  );
}
