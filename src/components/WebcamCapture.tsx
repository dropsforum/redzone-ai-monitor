"use client";

import React, { useRef, useEffect, forwardRef, useImperativeHandle, useState } from 'react';
import { RefreshCcw, CameraOff } from 'lucide-react';

interface WebcamCaptureProps {
  onFrame?: (canvas: HTMLCanvasElement) => void;
  width?: number;
  height?: number;
  deviceId?: string | null;
}

export interface WebcamCaptureHandle {
  getCanvas: () => HTMLCanvasElement | null;
  getVideo: () => HTMLVideoElement | null;
}

const WebcamCapture = forwardRef<WebcamCaptureHandle, WebcamCaptureProps>(({ 
  onFrame, 
  width = 1280, 
  height = 720,
  deviceId
}, ref) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);

  useImperativeHandle(ref, () => ({
    getCanvas: () => canvasRef.current,
    getVideo: () => videoRef.current,
  }));

  useEffect(() => {
    let stream: MediaStream | null = null;

    async function setupWebcam() {
      setError(null);

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setError('Browser Not Supported');
        return;
      }

      try {
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
        }

        const constraints: MediaStreamConstraints = {
          video: {
            width: { ideal: width },
            height: { ideal: height },
            ...(deviceId ? { deviceId: { exact: deviceId } } : { facingMode: 'user' })
          },
          audio: false
        };

        try {
          stream = await navigator.mediaDevices.getUserMedia(constraints);
        } catch (e) {
          console.warn("Retrying webcam with basic constraints...", e);
          stream = await navigator.mediaDevices.getUserMedia({
            video: true,
            audio: false
          });
        }

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err: any) {
        console.error("Critical error accessing webcam:", err);
        if (err.name === 'NotAllowedError') setError('Permission Denied');
        else if (err.name === 'NotFoundError') setError('Camera Not Found');
        else if (err.name === 'NotReadableError') setError('Camera In Use');
        else setError('Connection Error');
      }
    }

    setupWebcam();

    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [width, height, deviceId]);

  useEffect(() => {
    let animationId: number;

    const captureFrame = () => {
      if (videoRef.current && canvasRef.current && onFrame) {
        const video = videoRef.current;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

        if (ctx && video.readyState === video.HAVE_ENOUGH_DATA) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          onFrame(canvas);
        }
      }
      animationId = requestAnimationFrame(captureFrame);
    };

    animationId = requestAnimationFrame(captureFrame);

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [onFrame]);

  return (
    <div className="relative w-full h-full bg-slate-50 flex items-center justify-center border-slate-200">
      {error ? (
        <div className="flex flex-col items-center gap-4 p-8 text-center animate-in fade-in zoom-in duration-500">
          <div className="relative">
            <div className="p-5 bg-red-50 rounded-full text-red-500 border border-red-100">
              <CameraOff size={40} strokeWidth={1.5} />
            </div>
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-black text-slate-800 uppercase tracking-tighter italic">{error}</h3>
            <p className="text-slate-400 text-[10px] mt-1 max-w-[240px] leading-relaxed font-bold uppercase tracking-widest">
              {error === 'Permission Denied' 
                ? 'Check browser settings and click "Allow" for camera access.' 
                : error === 'Browser Not Supported'
                ? 'Camera access requires localhost or HTTPS connection.'
                : error === 'Camera In Use'
                ? 'Close other applications using the camera.'
                : 'Could not detect a working camera hardware.'}
            </p>
          </div>
          <button 
            onClick={() => window.location.reload()}
            className="mt-2 px-6 py-2 bg-slate-100 text-slate-600 text-[10px] font-black rounded-lg hover:bg-slate-200 active:scale-95 transition-all uppercase tracking-widest border border-slate-200 shadow-sm"
          >
            Reconnect System
          </button>
        </div>
      ) : (
        <>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-cover"
          />
          <canvas ref={canvasRef} className="hidden" />
          
          <div className="absolute top-4 left-4 flex items-center gap-2 px-2.5 py-1 bg-white/80 backdrop-blur-md rounded-full border border-slate-200 select-none shadow-sm">
            <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
            <span className="text-[9px] font-black text-slate-600 tracking-widest uppercase">Live Stream</span>
          </div>
        </>
      )}
    </div>
  );
});

WebcamCapture.displayName = "WebcamCapture";

export default WebcamCapture;
