"use client";

import React from 'react';
import { AlertCircle } from 'lucide-react';

interface AlertIndicatorProps {
  active: boolean;
}

const AlertIndicator: React.FC<AlertIndicatorProps> = ({ active }) => {
  if (!active) return null;

  return (
    <div className="absolute top-10 left-1/2 -translate-x-1/2 z-[100] flex items-center gap-3 px-8 py-4 bg-red-600 text-white rounded-2xl shadow-[0_0_50px_rgba(220,38,38,0.8)] animate-bounce border-4 border-white ring-4 ring-red-600/50">
      <AlertCircle className="w-8 h-8 animate-pulse" />
      <span className="text-2xl font-black uppercase tracking-[0.2em] italic">Red Zone Breach</span>
    </div>
  );
};

export default AlertIndicator;
