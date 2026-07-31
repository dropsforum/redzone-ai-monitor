"use client";

import React, {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from 'react';
import { CameraOff, UploadCloud, Video } from 'lucide-react';

export type VideoSourceMode = 'camera' | 'file';

export interface VideoFrameRect {
  left: number;
  top: number;
  width: number;
  height: number;
}

interface VideoFrameSourceProps {
  onFrame?: (canvas: HTMLCanvasElement) => void;
  onFrameRectChange?: (rect: VideoFrameRect) => void;
  width?: number;
  height?: number;
  deviceId?: string | null;
  sourceMode: VideoSourceMode;
  videoUrl?: string | null;
  videoLabel?: string | null;
  frameIntervalMs?: number;
  onVideoFileDrop?: (file: File) => void;
  onTimelineReset?: (reason: 'seek' | 'loop') => void;
}

export interface VideoFrameSourceHandle {
  getCanvas: () => HTMLCanvasElement | null;
  getVideo: () => HTMLVideoElement | null;
  pause: () => void;
  play: () => Promise<void>;
}

function getRenderedRect(
  containerWidth: number,
  containerHeight: number,
  videoWidth: number,
  videoHeight: number,
  fit: 'cover' | 'contain',
): VideoFrameRect {
  if (!containerWidth || !containerHeight || !videoWidth || !videoHeight) {
    return { left: 0, top: 0, width: containerWidth, height: containerHeight };
  }

  const scale = fit === 'cover'
    ? Math.max(containerWidth / videoWidth, containerHeight / videoHeight)
    : Math.min(containerWidth / videoWidth, containerHeight / videoHeight);
  const width = videoWidth * scale;
  const height = videoHeight * scale;

  return {
    left: (containerWidth - width) / 2,
    top: (containerHeight - height) / 2,
    width,
    height,
  };
}

function rectsMatch(a: VideoFrameRect, b: VideoFrameRect) {
  return Math.abs(a.left - b.left) < 0.5
    && Math.abs(a.top - b.top) < 0.5
    && Math.abs(a.width - b.width) < 0.5
    && Math.abs(a.height - b.height) < 0.5;
}

const VideoFrameSource = forwardRef<VideoFrameSourceHandle, VideoFrameSourceProps>(({
  onFrame,
  onFrameRectChange,
  width = 1280,
  height = 720,
  deviceId,
  sourceMode,
  videoUrl,
  videoLabel,
  frameIntervalMs = 100,
  onVideoFileDrop,
  onTimelineReset,
}, ref) => {
  const rootRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const lastFrameTimeRef = useRef(0);
  const lastPlaybackTimeRef = useRef(0);
  const [error, setError] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isDraggingVideo, setIsDraggingVideo] = useState(false);
  const [frameRect, setFrameRect] = useState<VideoFrameRect>({ left: 0, top: 0, width: 0, height: 0 });

  useImperativeHandle(ref, () => ({
    getCanvas: () => canvasRef.current,
    getVideo: () => videoRef.current,
    pause: () => {
      videoRef.current?.pause();
    },
    play: async () => {
      if (!videoRef.current) return;
      await videoRef.current.play();
    },
  }));

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach(track => track.stop());
    streamRef.current = null;
  }, []);

  const updateFrameRect = useCallback(() => {
    const root = rootRef.current;
    const video = videoRef.current;
    if (!root || !video) return;

    const fit = sourceMode === 'file' ? 'contain' : 'cover';
    const nextRect = getRenderedRect(
      root.clientWidth,
      root.clientHeight,
      video.videoWidth,
      video.videoHeight,
      fit,
    );

    setFrameRect(prev => {
      if (rectsMatch(prev, nextRect)) return prev;
      return nextRect;
    });
    onFrameRectChange?.(nextRect);
  }, [onFrameRectChange, sourceMode]);

  useEffect(() => {
    if (sourceMode !== 'camera') {
      stopStream();
      return;
    }

    let cancelled = false;

    async function setupWebcam() {
      setError(null);
      setIsReady(false);

      if (!navigator.mediaDevices?.getUserMedia) {
        setError('Browser Not Supported');
        return;
      }

      try {
        stopStream();

        const constraints: MediaStreamConstraints = {
          video: {
            width: { ideal: width },
            height: { ideal: height },
            ...(deviceId ? { deviceId: { exact: deviceId } } : { facingMode: 'user' }),
          },
          audio: false,
        };

        try {
          streamRef.current = await navigator.mediaDevices.getUserMedia(constraints);
        } catch (e) {
          console.warn('Retrying webcam with basic constraints...', e);
          streamRef.current = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        }

        if (cancelled) {
          stopStream();
          return;
        }

        if (videoRef.current) {
          videoRef.current.srcObject = streamRef.current;
          await videoRef.current.play().catch(() => undefined);
        }
      } catch (err: unknown) {
        console.error('Critical error accessing webcam:', err);
        const name = err instanceof DOMException ? err.name : '';
        if (name === 'NotAllowedError') setError('Permission Denied');
        else if (name === 'NotFoundError') setError('Camera Not Found');
        else if (name === 'NotReadableError') setError('Camera In Use');
        else setError('Connection Error');
      }
    }

    setupWebcam();

    return () => {
      cancelled = true;
      stopStream();
    };
  }, [deviceId, height, sourceMode, stopStream, width]);

  useEffect(() => {
    if (sourceMode !== 'file') return;

    stopStream();
    setError(null);
    setIsReady(false);

    const video = videoRef.current;
    if (!video) return;

    video.pause();
    video.defaultPlaybackRate = 1;
    video.playbackRate = 1;
    lastPlaybackTimeRef.current = 0;
    video.srcObject = null;
    if (videoUrl) {
      video.src = videoUrl;
      video.load();
    } else {
      video.removeAttribute('src');
      video.load();
    }
  }, [sourceMode, stopStream, videoUrl]);

  useEffect(() => {
    const root = rootRef.current;
    const video = videoRef.current;
    if (!root || !video) return;

    const observer = new ResizeObserver(updateFrameRect);
    observer.observe(root);
    video.addEventListener('loadedmetadata', updateFrameRect);
    window.addEventListener('resize', updateFrameRect);
    updateFrameRect();

    return () => {
      observer.disconnect();
      video.removeEventListener('loadedmetadata', updateFrameRect);
      window.removeEventListener('resize', updateFrameRect);
    };
  }, [updateFrameRect]);

  useEffect(() => {
    let animationId: number;

    const captureFrame = () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext('2d');
      const now = performance.now();

      if (
        sourceMode === 'file'
        && video
        && !video.seeking
        && video.currentTime + 0.25 < lastPlaybackTimeRef.current
      ) {
        onTimelineReset?.('loop');
      }
      if (video && sourceMode === 'file') {
        lastPlaybackTimeRef.current = video.currentTime;
      }

      if (
        video
        && canvas
        && ctx
        && onFrame
        && now - lastFrameTimeRef.current >= frameIntervalMs
        && video.readyState >= video.HAVE_CURRENT_DATA
        && video.videoWidth
        && video.videoHeight
      ) {
        lastFrameTimeRef.current = now;
        if (canvas.width !== video.videoWidth) canvas.width = video.videoWidth;
        if (canvas.height !== video.videoHeight) canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        onFrame(canvas);
      }

      animationId = requestAnimationFrame(captureFrame);
    };

    animationId = requestAnimationFrame(captureFrame);

    return () => {
      cancelAnimationFrame(animationId);
    };
  }, [frameIntervalMs, onFrame, onTimelineReset, sourceMode]);

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      videoRef.current.defaultPlaybackRate = 1;
      videoRef.current.playbackRate = 1;
    }
    setIsReady(true);
    updateFrameRect();
  };

  const frameStyle: React.CSSProperties = {
    left: frameRect.left,
    top: frameRect.top,
    width: frameRect.width || '100%',
    height: frameRect.height || '100%',
  };

  const handleDragEvent = (event: React.DragEvent<HTMLDivElement>) => {
    if (sourceMode !== 'file') return;
    event.preventDefault();
    event.stopPropagation();
  };

  const handleDragEnter = (event: React.DragEvent<HTMLDivElement>) => {
    handleDragEvent(event);
    if (sourceMode === 'file') setIsDraggingVideo(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    handleDragEvent(event);
    if (event.currentTarget.contains(event.relatedTarget as Node | null)) return;
    setIsDraggingVideo(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    handleDragEvent(event);
    setIsDraggingVideo(false);
    if (sourceMode !== 'file') return;

    const droppedFile = Array.from(event.dataTransfer.files).find(file => (
      file.type.startsWith('video/') || /\.(mp4|mov|m4v|webm|ogv|ogg)$/i.test(file.name)
    ));
    if (droppedFile) onVideoFileDrop?.(droppedFile);
  };

  return (
    <div
      ref={rootRef}
      className={`relative w-full h-full bg-slate-50 flex items-center justify-center overflow-hidden border-slate-200 transition-colors ${
        isDraggingVideo ? 'bg-[#55799a]/10 ring-2 ring-inset ring-[#55799a]' : ''
      }`}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragEvent}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {error ? (
        <div className="flex flex-col items-center gap-4 p-8 text-center animate-in fade-in zoom-in duration-500">
          <div className="p-5 bg-red-50 rounded-full text-red-500 border border-red-100">
            <CameraOff size={40} strokeWidth={1.5} />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-black text-slate-800 uppercase tracking-tighter italic">{error}</h3>
            <p className="text-slate-400 text-[10px] mt-1 max-w-[240px] leading-relaxed font-bold uppercase tracking-widest">
              {error === 'Permission Denied'
                ? 'Check browser settings and click Allow for camera access.'
                : error === 'Browser Not Supported'
                  ? 'Camera access requires localhost or HTTPS connection.'
                  : error === 'Camera In Use'
                    ? 'Close other applications using the camera.'
                    : 'Could not detect a working camera or video source.'}
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
          {sourceMode === 'file' && (!videoUrl || isDraggingVideo) && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 p-8 text-center">
              <div className="p-5 bg-white rounded-full text-[#55799a] border border-slate-100 shadow-sm">
                <UploadCloud size={40} strokeWidth={1.5} />
              </div>
              <div>
                <h3 className="text-sm font-black text-slate-700 uppercase tracking-widest">
                  {isDraggingVideo ? 'Drop Video' : 'Choose Recorded Video'}
                </h3>
              </div>
            </div>
          )}

          <video
            ref={videoRef}
            autoPlay={sourceMode === 'camera'}
            controls={sourceMode === 'file' && Boolean(videoUrl)}
            loop={sourceMode === 'file'}
            playsInline
            muted={sourceMode === 'camera'}
            onLoadedMetadata={handleLoadedMetadata}
            onSeeking={() => {
              if (sourceMode === 'file') {
                lastPlaybackTimeRef.current = videoRef.current?.currentTime ?? 0;
                onTimelineReset?.('seek');
              }
            }}
            onEnded={() => {
              if (sourceMode === 'file') onTimelineReset?.('loop');
            }}
            className="absolute max-w-none max-h-none"
            style={frameStyle}
          />
          <canvas ref={canvasRef} className="hidden" />

          {(sourceMode === 'camera' || videoUrl) && isReady && (
            <div className="absolute top-4 left-4 flex items-center gap-2 px-2.5 py-1 bg-white/80 backdrop-blur-md rounded-full border border-slate-200 select-none shadow-sm">
              <div className={`w-1.5 h-1.5 rounded-full ${sourceMode === 'camera' ? 'bg-red-500 animate-pulse' : 'bg-[#55799a]'}`} />
              {sourceMode === 'camera' ? (
                <span className="text-[9px] font-black text-slate-600 tracking-widest uppercase">Live Stream</span>
              ) : (
                <>
                  <Video className="w-3 h-3 text-[#55799a]" />
                  <span className="max-w-[220px] truncate text-[9px] font-black text-slate-600 tracking-widest uppercase">
                    {videoLabel || 'Recorded Video'}
                  </span>
                </>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
});

VideoFrameSource.displayName = 'VideoFrameSource';

export default VideoFrameSource;
