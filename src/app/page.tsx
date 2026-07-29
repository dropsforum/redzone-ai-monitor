"use client";

import React, { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Play, Square, Edit3, RefreshCcw, Camera, Settings, Zap, Cpu, Volume2, VolumeX, Smartphone, Monitor, Video, UploadCloud, BarChart3, Download } from 'lucide-react';
import VideoFrameSource, { VideoFrameRect, VideoFrameSourceHandle, VideoSourceMode } from '../components/VideoFrameSource';
import ZoneEditor, { Point } from '../components/ZoneEditor';
import DetectionOverlay from '../components/DetectionOverlay';
import TrafficLight, { TrafficLightState } from '../components/TrafficLight';
import { YoloDetector, Detection } from '../lib/yolo-detector';
import { isPersonInZone, isPersonNearZone } from '../lib/zone-checker';
import { AlertManager } from '../lib/alert-manager';
import {
  BreachAggregateMode,
  BreachRecorder,
  BreachSnapshot,
  breachMetricsToCsv,
  breachSegmentsToCsv,
  formatBucketLabel,
  formatDuration,
} from '../lib/breach-recorder';

type BreachReportTab = 'records' | 'metrics';

function HomeContent() {
  // App State
  const searchParams = useSearchParams();
  const isEmbedMode = searchParams.get('embed') === 'true';
  
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isModelLoaded, setIsModelLoaded] = useState(false);
  const [modelError, setModelError] = useState<string | null>(null);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [isMobileMode] = useState(() => (
    typeof navigator !== 'undefined' && /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
  ));
  const [fps, setFps] = useState(0);
  const [sourceMode, setSourceMode] = useState<VideoSourceMode>('camera');
  
  // Data State
  const [detections, setDetections] = useState<Detection[]>([]);
  const [zone, setZone] = useState<Point[]>([]);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [trafficLightState, setTrafficLightState] = useState<TrafficLightState>('green');
  
  // Camera State
  const [availableDevices, setAvailableDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [videoFileName, setVideoFileName] = useState<string | null>(null);
  const [frameRect, setFrameRect] = useState<VideoFrameRect>({ left: 0, top: 0, width: 0, height: 0 });
  
  // Detection Settings
  const [warningBuffer, setWarningBuffer] = useState(0.1); // normalized distance 0.0 - 0.3
  const [breachAggregateMode, setBreachAggregateMode] = useState<BreachAggregateMode>('minute');
  const [breachReportTab, setBreachReportTab] = useState<BreachReportTab>('records');

  // Refs
  const detectorRef = useRef<YoloDetector | null>(null);
  const alertManagerRef = useRef<AlertManager>(new AlertManager(5));
  const breachRecorderRef = useRef<BreachRecorder>(new BreachRecorder());
  const videoSourceRef = useRef<VideoFrameSourceHandle>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoObjectUrlRef = useRef<string | null>(null);
  const lastProcessedTimeRef = useRef<number>(0);
  const frameCountRef = useRef<number>(0);
  const lastFpsUpdateRef = useRef<number>(0);
  const [breachSnapshot, setBreachSnapshot] = useState<BreachSnapshot>(() => new BreachRecorder().snapshot('minute'));

  const refreshBreachSnapshot = useCallback(() => {
    setBreachSnapshot(breachRecorderRef.current.snapshot(breachAggregateMode));
  }, [breachAggregateMode]);

  const resetRuntimeState = useCallback(() => {
    setIsMonitoring(false);
    setDetections([]);
    setTrafficLightState('green');
    setDimensions({ width: 0, height: 0 });
    setFrameRect({ left: 0, top: 0, width: 0, height: 0 });
    setFps(0);
    frameCountRef.current = 0;
    lastProcessedTimeRef.current = 0;
    lastFpsUpdateRef.current = 0;
    breachRecorderRef.current.reset();
    setBreachSnapshot(breachRecorderRef.current.snapshot(breachAggregateMode));
  }, [breachAggregateMode]);

  useEffect(() => {
    refreshBreachSnapshot();
  }, [refreshBreachSnapshot]);

  useEffect(() => {
    if (!isMonitoring) return;
    const timer = window.setInterval(refreshBreachSnapshot, 1000);
    return () => window.clearInterval(timer);
  }, [isMonitoring, refreshBreachSnapshot]);

  const clearRecordedVideo = useCallback(() => {
    if (videoObjectUrlRef.current) {
      URL.revokeObjectURL(videoObjectUrlRef.current);
      videoObjectUrlRef.current = null;
    }
    setVideoUrl(null);
    setVideoFileName(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  }, []);

  const handleSourceModeChange = useCallback((nextMode: VideoSourceMode) => {
    if (nextMode === sourceMode) return;
    resetRuntimeState();
    setIsDrawing(false);
    setSourceMode(nextMode);
    if (nextMode === 'camera') clearRecordedVideo();
  }, [clearRecordedVideo, resetRuntimeState, sourceMode]);

  const loadRecordedVideo = useCallback((file: File) => {
    resetRuntimeState();
    setIsDrawing(false);
    clearRecordedVideo();

    const nextUrl = URL.createObjectURL(file);
    videoObjectUrlRef.current = nextUrl;
    setVideoUrl(nextUrl);
    setVideoFileName(file.name);
    setSourceMode('file');
  }, [clearRecordedVideo, resetRuntimeState]);

  const handleVideoFileChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    loadRecordedVideo(file);
  }, [loadRecordedVideo]);

  const exportBreachCsv = useCallback(() => {
    const csv = breachReportTab === 'records'
      ? breachSegmentsToCsv(breachSnapshot.segments)
      : breachMetricsToCsv(breachSnapshot, breachAggregateMode);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `drops-breach-${breachReportTab}-${Date.now()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }, [breachAggregateMode, breachReportTab, breachSnapshot]);

  useEffect(() => {
    return () => {
      if (videoObjectUrlRef.current) URL.revokeObjectURL(videoObjectUrlRef.current);
    };
  }, []);

  // Screenshot Logic
  const captureScreenshot = useCallback(() => {
    if (!videoSourceRef.current || !dimensions.width) return;

    const video = videoSourceRef.current.getVideo();
    if (!video) return;

    const canvas = document.createElement('canvas');
    canvas.width = dimensions.width;
    canvas.height = dimensions.height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 1. Draw Video Frame
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // 2. Draw Zone
    if (zone.length >= 3) {
      ctx.beginPath();
      ctx.moveTo(zone[0].x * canvas.width, zone[0].y * canvas.height);
      for (let i = 1; i < zone.length; i++) {
        ctx.lineTo(zone[i].x * canvas.width, zone[i].y * canvas.height);
      }
      ctx.closePath();
      ctx.fillStyle = 'rgba(220, 38, 38, 0.3)';
      ctx.fill();
      ctx.strokeStyle = '#dc2626';
      ctx.lineWidth = 4;
      ctx.stroke();
    }

    // 3. Draw Detections
    detections.forEach(det => {
      ctx.strokeStyle = '#55799a';
      ctx.lineWidth = 3;
      ctx.strokeRect(det.x1, det.y1, det.x2 - det.x1, det.y2 - det.y1);
      
      // Label background
      ctx.fillStyle = '#55799a';
      const label = `PERSON ${Math.round(det.confidence * 100)}%`;
      ctx.font = 'bold 12px sans-serif';
      const textWidth = ctx.measureText(label).width;
      ctx.fillRect(det.x1, det.y1 - 20, textWidth + 10, 20);
      
      // Label text
      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, det.x1 + 5, det.y1 - 5);
    });

    // 4. Add Watermark
    const watermarkText = 'powered by dropsforum.org';
    
    // Large centered watermark with 5% transparency
    ctx.save();
    ctx.font = 'bold 48px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = 'rgba(85, 121, 154, 0.1)'; // #55799a with 10% alpha
    ctx.fillText(watermarkText, canvas.width / 2, canvas.height / 2);
    ctx.restore();

    // 5. Download
    const link = document.createElement('a');
    link.download = `drops-monitor-capture-${Date.now()}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  }, [dimensions, zone, detections]);

  // Enumerate cameras
  const getDevices = useCallback(async (requestPermission = false) => {
    try {
      if (!navigator.mediaDevices) return;

      if (requestPermission) {
        // Explicitly request permission to trigger browser device discovery
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        stream.getTracks().forEach(track => track.stop());
      }
      
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(device => device.kind === 'videoinput');
      
      console.log('[CAMERA] Found devices:', videoDevices.map(d => d.label || 'Unnamed Device'));
      setAvailableDevices(videoDevices);
      
      if (videoDevices.length > 0 && !selectedDeviceId) {
        setSelectedDeviceId(videoDevices[0].deviceId);
      }
    } catch (err) {
      console.error("Error enumerating devices:", err);
    }
  }, [selectedDeviceId]);

  useEffect(() => {
    if (!navigator.mediaDevices) return;

    const handleDeviceChange = () => {
      void getDevices();
    };

    // Initial scan
    const initialScan = setTimeout(() => void getDevices(), 0);
    
    // Re-scan after a short delay to catch Continuity Cameras/iPhone
    const timer = setTimeout(() => void getDevices(), 2000);
    
    // Listen for hardware changes
    navigator.mediaDevices.addEventListener('devicechange', handleDeviceChange);
    
    return () => {
      clearTimeout(initialScan);
      clearTimeout(timer);
      navigator.mediaDevices.removeEventListener('devicechange', handleDeviceChange);
    };
  }, [getDevices]);

  // Initialize Detector
  useEffect(() => {
    const init = async () => {
      try {
        const detector = new YoloDetector();
        await detector.init('/models/yolo26n.onnx');
        detectorRef.current = detector;
        setIsModelLoaded(true);
        setModelError(null);
      } catch (error) {
        console.error('[APP] Failed to initialize detector:', error);
        setModelError('Generate public/models/yolo26n.onnx before monitoring.');
      }
    };
    void init();
  }, []);

  // Update dimensions when video loads
  const handleFrame = useCallback((canvas: HTMLCanvasElement) => {
    if (dimensions.width !== canvas.width || dimensions.height !== canvas.height) {
      setDimensions({ width: canvas.width, height: canvas.height });
    }

    if (!isMonitoring || !isModelLoaded || !detectorRef.current) {
      setTrafficLightState('green');
      return;
    }

    const now = Date.now();
    // Throttling: Desktop ~10 FPS (100ms), Mobile ~3 FPS (333ms)
    const throttle = isMobileMode ? 333 : 100;
    
    if (now - lastProcessedTimeRef.current >= throttle) {
      lastProcessedTimeRef.current = now;
      
      detectorRef.current.detect(canvas).then(results => {
        setDetections(results);
        
        let personInZone = false;

        // Check for zone alerts
        if (zone.length >= 3 && results.length > 0) {
          personInZone = results.some(det => {
            const inZone = isPersonInZone(det, zone, canvas.width, canvas.height, true);
            return inZone;
          });

          if (personInZone) {
            setTrafficLightState('red');
            alertManagerRef.current.trigger(isAudioEnabled).catch(e => console.error('[APP] Alert trigger failed:', e));
          } else {
            // Yellow: person is near or partially in zone
            const personNearZone = results.some(det => isPersonNearZone(det, zone, canvas.width, canvas.height, warningBuffer));
            setTrafficLightState(personNearZone ? 'yellow' : 'green');
          }
        } else {
          // Green: no zone or no detections
          setTrafficLightState('green');
        }

        breachRecorderRef.current.update(personInZone, Date.now());
        refreshBreachSnapshot();

        // FPS Calculation
        frameCountRef.current++;
        if (now - lastFpsUpdateRef.current >= 1000) {
          setFps(frameCountRef.current);
          frameCountRef.current = 0;
          lastFpsUpdateRef.current = now;
        }
      });
    }
  }, [isMonitoring, isModelLoaded, zone, isAudioEnabled, isMobileMode, dimensions, warningBuffer, refreshBreachSnapshot]);

  const overlayStyle: React.CSSProperties = {
    left: frameRect.left,
    top: frameRect.top,
    width: frameRect.width || '100%',
    height: frameRect.height || '100%',
  };
  const hasActiveVideoSource = Boolean(dimensions.width && dimensions.height && (sourceMode === 'camera' || videoUrl));

  return (
    <main className={`bg-white text-slate-800 flex flex-col p-4 md:p-6 font-sans mx-auto ${isEmbedMode ? 'max-w-none w-full' : 'max-w-[700px]'}`}>
      {/* Header */}
      {!isEmbedMode && (
        <div className="flex flex-col gap-2 mb-6 border-b border-slate-100 pb-4">
          <div className="flex justify-between items-center">
            <h1 className="text-xl font-black tracking-tighter text-[#55799a] uppercase italic text-center md:text-left">
              DROPS FORUM RED ZONE MONITOR POC
            </h1>
            <div className="flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-full px-3 py-1">
              <Cpu className="w-3 h-3 text-[#55799a]" />
              <span className="text-[10px] font-bold uppercase text-slate-600">{isModelLoaded ? 'AI Ready' : modelError ? 'Model Missing' : 'Loading...'}</span>
            </div>
          </div>
          <p className="text-slate-400 text-[10px] font-mono flex items-center gap-2 uppercase tracking-widest">
            <Zap className="w-3 h-3 text-[#55799a]" /> POWERED BY YOLO26 AI • BROWSER-NATIVE
          </p>
        </div>
      )}

      <div className="space-y-6">
        {/* Monitoring Panel */}
        <div className="space-y-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1 shadow-sm">
              <button
                type="button"
                onClick={() => handleSourceModeChange('camera')}
                className={`h-9 px-3 flex items-center gap-2 rounded-md text-[10px] font-black uppercase tracking-widest transition-all ${
                  sourceMode === 'camera' ? 'bg-white text-[#55799a] shadow-sm' : 'text-slate-400 hover:text-slate-600'
                }`}
              >
                <Camera className="w-3.5 h-3.5" />
                Live Camera
              </button>
              <button
                type="button"
                onClick={() => handleSourceModeChange('file')}
                className={`h-9 px-3 flex items-center gap-2 rounded-md text-[10px] font-black uppercase tracking-widest transition-all ${
                  sourceMode === 'file' ? 'bg-white text-[#55799a] shadow-sm' : 'text-slate-400 hover:text-slate-600'
                }`}
              >
                <Video className="w-3.5 h-3.5" />
                Recorded Video
              </button>
            </div>

            {sourceMode === 'file' && (
              <div className="flex items-center gap-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/*"
                  onChange={handleVideoFileChange}
                  className="hidden"
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="h-9 px-3 flex items-center gap-2 rounded-lg border border-slate-200 bg-white text-[#55799a] text-[10px] font-black uppercase tracking-widest shadow-sm hover:bg-slate-50 transition-all"
                >
                  <UploadCloud className="w-3.5 h-3.5" />
                  {videoFileName ? 'Replace Video' : 'Choose Video'}
                </button>
                {videoFileName && (
                  <span className="max-w-[220px] truncate text-[10px] font-mono text-slate-400">
                    {videoFileName}
                  </span>
                )}
              </div>
            )}
          </div>

          <div className="relative aspect-video bg-slate-50 rounded-xl overflow-hidden border border-slate-200 shadow-sm ring-1 ring-slate-100">
            {/* Components Layered */}
            <VideoFrameSource
              ref={videoSourceRef}
              onFrame={handleFrame}
              onFrameRectChange={setFrameRect}
              width={isMobileMode ? 640 : 1280}
              height={isMobileMode ? 480 : 720}
              deviceId={selectedDeviceId}
              sourceMode={sourceMode}
              videoUrl={videoUrl}
              videoLabel={videoFileName}
              frameIntervalMs={isMobileMode ? 333 : 100}
              onVideoFileDrop={loadRecordedVideo}
            />

            {hasActiveVideoSource && (
              <div className="absolute z-20" style={overlayStyle}>
                <ZoneEditor 
                  width={dimensions.width} 
                  height={dimensions.height} 
                  isDrawing={isDrawing}
                  onZoneChange={setZone}
                  initialPoints={zone}
                />

                <DetectionOverlay 
                  detections={detections}
                  width={dimensions.width}
                  height={dimensions.height}
                />
              </div>
            )}
            
            {isMonitoring && <TrafficLight state={trafficLightState} />}

            {/* Empty State / Loading */}
            {!isModelLoaded && (
              <div className="absolute inset-0 bg-white/90 backdrop-blur-sm z-[60] flex flex-col items-center justify-center">
                {!modelError && <div className="w-10 h-10 border-4 border-[#55799a] border-t-transparent rounded-full animate-spin mb-4" />}
                <p className="text-[#55799a] font-black tracking-widest uppercase text-xs">{modelError ? 'Model Missing' : 'Initializing AI'}</p>
                {modelError && (
                  <p className="mt-2 max-w-xs text-center text-[10px] leading-relaxed text-slate-400">
                    {modelError}
                  </p>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-slate-400">
                {isMobileMode ? <Smartphone className="w-3 h-3" /> : <Monitor className="w-3 h-3" />}
                <span className="text-[10px] font-mono font-bold">{fps} FPS</span>
              </div>
              <button 
                onClick={() => setIsAudioEnabled(!isAudioEnabled)}
                className={`transition-colors ${isAudioEnabled ? 'text-[#55799a]' : 'text-slate-300'}`}
              >
                {isAudioEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Controls Footer */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={async () => {
                await alertManagerRef.current.unlockAudio();
                const nextMonitoring = !isMonitoring;

                if (nextMonitoring) {
                  setIsDrawing(false);
                }

                if (sourceMode === 'file') {
                  if (nextMonitoring) {
                    await videoSourceRef.current?.play().catch(e => console.error('[APP] Recorded video playback failed:', e));
                  } else {
                    videoSourceRef.current?.pause();
                  }
                }

                setIsMonitoring(nextMonitoring);
                if (nextMonitoring) {
                  breachRecorderRef.current.start(Date.now());
                } else {
                  breachRecorderRef.current.stop(Date.now());
                  setTrafficLightState('green');
                }
                refreshBreachSnapshot();
              }}
              disabled={!isModelLoaded || zone.length < 3 || !hasActiveVideoSource}
              className={`flex-1 min-w-[140px] h-12 flex items-center justify-center gap-2 rounded-xl font-bold transition-all ${
                isMonitoring 
                ? 'bg-slate-100 text-slate-500 hover:bg-slate-200' 
                : `bg-[#55799a] text-white shadow-md shadow-[#55799a]/20 hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-50 disabled:translate-y-0 ${zone.length >= 3 && !isDrawing && !isMonitoring ? 'animate-subtle-blink shadow-[#55799a]/40' : ''}`
              }`}
            >
              {isMonitoring ? <Square className="w-4 h-4 fill-current" /> : <Play className="w-4 h-4 fill-current" />}
              <span className="uppercase text-[10px] tracking-widest">{isMonitoring ? 'Stop' : 'Start Monitor'}</span>
            </button>

            <button
              onClick={() => {
                setIsDrawing(!isDrawing);
                if (!isDrawing) {
                  setIsMonitoring(false);
                  if (sourceMode === 'file') videoSourceRef.current?.pause();
                }
              }}
              disabled={!hasActiveVideoSource}
              className={`flex-1 min-w-[140px] h-12 flex items-center justify-center gap-2 rounded-xl font-bold transition-all border-2 ${
                isDrawing 
                ? `bg-red-50 border-red-500 text-red-500 ${zone.length >= 3 ? 'animate-subtle-blink border-red-600 shadow-md' : ''}` 
                : `bg-white border-[#55799a] text-[#55799a] hover:bg-slate-50 shadow-sm ${zone.length === 0 && hasActiveVideoSource ? 'animate-subtle-blink shadow-[#55799a]/20' : ''}`
              }`}
            >
              <Edit3 className="w-4 h-4" />
              <span className="uppercase text-[10px] tracking-widest">{isDrawing ? 'Save Zone' : 'Draw Zone'}</span>
            </button>
            
            <button
              onClick={captureScreenshot}
              disabled={!hasActiveVideoSource}
              className={`flex-1 min-w-[140px] h-12 flex items-center justify-center gap-2 rounded-xl font-bold text-[10px] bg-white border border-slate-200 text-[#55799a] hover:bg-slate-50 transition-all shadow-sm uppercase tracking-widest ${isMonitoring ? 'animate-subtle-blink ring-1 ring-[#55799a]/20' : ''}`}
              title="Capture Screenshot"
            >
              <Camera className="w-4 h-4" />
              <span>Screenshot</span>
            </button>
            
            <button
              onClick={async () => {
                await alertManagerRef.current.unlockAudio();
                await alertManagerRef.current.trigger(true);
              }}
              className="flex-1 min-w-[140px] h-12 flex items-center justify-center gap-2 rounded-xl font-bold text-[10px] bg-yellow-500 text-white hover:bg-yellow-600 transition-all shadow-md shadow-yellow-500/20 hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 uppercase tracking-widest"
              title="Test Alert Sound"
            >
              <Volume2 className="w-4 h-4" />
              <span>Test Sound</span>
            </button>
          </div>
        </div>

        {/* Breach Recording */}
        <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm space-y-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-[#55799a]" />
              <div>
                <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500">Breach Time</h2>
                <p className="text-[9px] text-slate-400">Records breach and no-breach periods with dated start and end times.</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => {
                  breachRecorderRef.current.reset();
                  if (isMonitoring) breachRecorderRef.current.start(Date.now());
                  setBreachSnapshot(breachRecorderRef.current.snapshot(breachAggregateMode));
                }}
                className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-slate-100 text-[#55799a] hover:bg-slate-50"
                title="Reset breach recording"
              >
                <RefreshCcw className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={exportBreachCsv}
                disabled={breachSnapshot.segments.length === 0}
                className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-slate-100 text-[#55799a] hover:bg-slate-50 disabled:opacity-40"
                title={`Export ${breachReportTab} CSV`}
              >
                <Download className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1 shadow-sm">
            {(['records', 'metrics'] as BreachReportTab[]).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setBreachReportTab(tab)}
                className={`h-8 px-3 rounded-md text-[10px] font-black uppercase tracking-widest transition-all ${
                  breachReportTab === tab ? 'bg-white text-[#55799a] shadow-sm' : 'text-slate-400 hover:text-slate-600'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          {breachReportTab === 'records' ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-xl bg-red-50 border border-red-100 p-3">
                  <div className="text-[8px] uppercase tracking-widest font-black text-red-300">Breach Records</div>
                  <div className="text-lg font-black text-red-500">{breachSnapshot.breachCount}</div>
                </div>
                <div className="rounded-xl bg-green-50 border border-green-100 p-3">
                  <div className="text-[8px] uppercase tracking-widest font-black text-green-400">No-Breach Records</div>
                  <div className="text-lg font-black text-green-600">{breachSnapshot.clearCount}</div>
                </div>
              </div>

              <div className="max-h-56 overflow-auto rounded-xl border border-slate-100">
                <table className="w-full text-left text-[9px]">
                  <thead className="sticky top-0 bg-slate-50 text-slate-400 uppercase tracking-widest">
                    <tr>
                      <th className="px-3 py-2">State</th>
                      <th className="px-3 py-2">Start</th>
                      <th className="px-3 py-2">End</th>
                      <th className="px-3 py-2 text-right">Duration</th>
                    </tr>
                  </thead>
                  <tbody className="font-mono text-slate-500">
                    {breachSnapshot.segments.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-3 py-8 text-center uppercase tracking-widest text-slate-300 font-black">
                          Start monitoring to record breach and no-breach periods
                        </td>
                      </tr>
                    ) : (
                      breachSnapshot.segments.slice(-20).map((segment, index) => (
                        <tr key={`${segment.startMs}-${index}`} className="border-t border-slate-100">
                          <td className={`px-3 py-2 font-black ${segment.state === 'breach' ? 'text-red-500' : 'text-green-600'}`}>
                            {segment.state === 'breach' ? 'BREACH' : 'NO BREACH'}
                          </td>
                          <td className="px-3 py-2">{new Date(segment.startMs).toLocaleString()}</td>
                          <td className="px-3 py-2">{new Date(segment.endMs).toLocaleString()}</td>
                          <td className="px-3 py-2 text-right">{formatDuration(segment.endMs - segment.startMs)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex justify-end">
                <select
                  value={breachAggregateMode}
                  onChange={(event) => setBreachAggregateMode(event.target.value as BreachAggregateMode)}
                  className="h-8 bg-slate-50 border border-slate-100 rounded-lg px-2 text-[10px] font-mono text-slate-600 outline-none focus:ring-1 focus:ring-[#55799a]"
                >
                  <option value="minute">Minute</option>
                  <option value="hour">Hour</option>
                </select>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div className="rounded-xl bg-slate-50 border border-slate-100 p-3">
                  <div className="text-[8px] uppercase tracking-widest font-black text-slate-400">Breach</div>
                  <div className="text-lg font-black text-red-500">{formatDuration(breachSnapshot.totalBreachMs)}</div>
                </div>
                <div className="rounded-xl bg-slate-50 border border-slate-100 p-3">
                  <div className="text-[8px] uppercase tracking-widest font-black text-slate-400">Rate</div>
                  <div className="text-lg font-black text-[#55799a]">
                    {breachSnapshot.totalMs > 0 ? `${Math.round((breachSnapshot.totalBreachMs / breachSnapshot.totalMs) * 100)}%` : '0%'}
                  </div>
                </div>
                <div className="rounded-xl bg-slate-50 border border-slate-100 p-3">
                  <div className="text-[8px] uppercase tracking-widest font-black text-slate-400">Observed</div>
                  <div className="text-lg font-black text-slate-700">{formatDuration(breachSnapshot.totalMs)}</div>
                </div>
              </div>

              <div className="h-32 rounded-xl border border-slate-100 bg-slate-50 px-3 pt-3 pb-7">
                {breachSnapshot.buckets.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-[10px] uppercase tracking-widest font-black text-slate-300">
                    Start monitoring to produce metrics
                  </div>
                ) : (
                  <div className="h-full flex items-end gap-1">
                    {breachSnapshot.buckets.slice(-18).map((bucket) => (
                      <div key={bucket.startMs} className="relative flex-1 h-full flex items-end">
                        <div className="absolute inset-x-0 bottom-0 bg-slate-200/70 rounded-t-sm" style={{ height: `${Math.max(3, (bucket.totalMs / (breachAggregateMode === 'hour' ? 3_600_000 : 60_000)) * 100)}%` }} />
                        <div className="absolute inset-x-0 bottom-0 bg-red-500 rounded-t-sm" style={{ height: `${Math.max(bucket.breachMs > 0 ? 3 : 0, bucket.breachPercent)}%` }} />
                        <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[7px] font-mono text-slate-400 whitespace-nowrap">
                          {formatBucketLabel(bucket.startMs, breachAggregateMode)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-[9px] font-black uppercase tracking-widest text-slate-500">
                    Aggregated Report
                  </h3>
                  <span className="text-[8px] font-mono uppercase tracking-widest text-slate-300">
                    By {breachAggregateMode}
                  </span>
                </div>
                <div className="max-h-56 overflow-auto rounded-xl border border-slate-100">
                  <table className="w-full text-left text-[9px]">
                    <thead className="sticky top-0 bg-slate-50 text-slate-400 uppercase tracking-widest">
                      <tr>
                        <th className="px-3 py-2">Bucket Start</th>
                        <th className="px-3 py-2">Bucket End</th>
                        <th className="px-3 py-2 text-right">Breach</th>
                        <th className="px-3 py-2 text-right">No Breach</th>
                        <th className="px-3 py-2 text-right">Total</th>
                        <th className="px-3 py-2 text-right">Breach %</th>
                      </tr>
                    </thead>
                    <tbody className="font-mono text-slate-500">
                      {breachSnapshot.buckets.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="px-3 py-8 text-center uppercase tracking-widest text-slate-300 font-black">
                            No aggregated report yet
                          </td>
                        </tr>
                      ) : (
                        breachSnapshot.buckets.slice(-60).map((bucket) => (
                          <tr key={bucket.startMs} className="border-t border-slate-100">
                            <td className="px-3 py-2">{new Date(bucket.startMs).toLocaleString()}</td>
                            <td className="px-3 py-2">{new Date(bucket.endMs).toLocaleString()}</td>
                            <td className="px-3 py-2 text-right text-red-500 font-black">{(bucket.breachMs / 1000).toFixed(2)}s</td>
                            <td className="px-3 py-2 text-right text-green-600 font-black">{(bucket.clearMs / 1000).toFixed(2)}s</td>
                            <td className="px-3 py-2 text-right">{(bucket.totalMs / 1000).toFixed(2)}s</td>
                            <td className="px-3 py-2 text-right">{bucket.breachPercent.toFixed(2)}%</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[9px] font-mono text-slate-400">
                <span className="px-2 py-1 rounded-lg border border-slate-100 bg-slate-50">
                  Period start: {breachSnapshot.periodStartMs ? new Date(breachSnapshot.periodStartMs).toLocaleString() : 'None'}
                </span>
                <span className="px-2 py-1 rounded-lg border border-slate-100 bg-slate-50">
                  Period end: {breachSnapshot.periodEndMs ? new Date(breachSnapshot.periodEndMs).toLocaleString() : 'None'}
                </span>
                <span className={`px-2 py-1 rounded-lg border ${breachSnapshot.currentState === 'breach' ? 'bg-red-50 text-red-500 border-red-100' : 'bg-green-50 text-green-600 border-green-100'}`}>
                  Current: {breachSnapshot.currentState === 'breach' ? `Breach ${formatDuration(breachSnapshot.activeBreachMs)}` : 'Clear'}
                </span>
                <span className="px-2 py-1 rounded-lg border border-slate-100 bg-slate-50">
                  Clear: {formatDuration(breachSnapshot.totalClearMs)}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Info & Settings Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Sensitivity Settings */}
          <div className="space-y-3 bg-white p-5 rounded-2xl border border-slate-100 shadow-sm">
            <div className="flex justify-between items-center text-[9px] uppercase font-black text-slate-400">
              <span className="flex items-center gap-2">
                <Zap className="w-3 h-3 text-[#55799a]" /> Orange Light Sensitivity
              </span>
              <span className="text-[#55799a] font-mono bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
                {Math.round(warningBuffer * 100)}%
              </span>
            </div>
            <input 
              type="range" 
              min="0.01" 
              max="0.3" 
              step="0.01" 
              value={warningBuffer}
              onChange={(e) => setWarningBuffer(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#55799a]"
            />
            <p className="text-[8px] text-slate-400 italic leading-tight">Controls how close a person must be to the red zone to trigger the yellow warning light.</p>
          </div>

          {/* System Info Panel */}
          {sourceMode === 'camera' ? (
            <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-[9px] text-slate-400 uppercase font-black tracking-widest flex items-center gap-2">
                  <Settings className="w-3 h-3 text-[#55799a]" /> Active Camera
                </span>
                <button 
                  onClick={() => getDevices(true)}
                  className="text-[#55799a] hover:bg-slate-50 p-1 rounded-md transition-all border border-transparent hover:border-slate-100"
                  title="Refresh Hardware"
                >
                  <RefreshCcw className="w-2.5 h-2.5" />
                </button>
              </div>
              <select 
                value={selectedDeviceId || ''} 
                onChange={(e) => setSelectedDeviceId(e.target.value)}
                className="w-full bg-slate-50 border border-slate-100 rounded-lg px-3 py-2 text-[10px] font-mono text-slate-600 outline-none focus:ring-1 focus:ring-[#55799a] transition-all cursor-pointer"
              >
                {availableDevices.length === 0 ? (
                  <option value="">Searching...</option>
                ) : (
                  availableDevices.map((device, idx) => (
                    <option key={device.deviceId + idx} value={device.deviceId}>
                      {device.label || `Camera ${idx + 1}`}
                    </option>
                  ))
                )}
              </select>
            </div>
          ) : (
            <div className="bg-white p-5 rounded-2xl border border-slate-100 shadow-sm space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-[9px] text-slate-400 uppercase font-black tracking-widest flex items-center gap-2">
                  <Video className="w-3 h-3 text-[#55799a]" /> Recorded Video
                </span>
                {videoUrl && (
                  <button
                    onClick={() => {
                      resetRuntimeState();
                      clearRecordedVideo();
                    }}
                    className="text-[#55799a] hover:bg-slate-50 p-1 rounded-md transition-all border border-transparent hover:border-slate-100"
                    title="Clear Video"
                  >
                    <RefreshCcw className="w-2.5 h-2.5" />
                  </button>
                )}
              </div>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="w-full h-10 px-3 flex items-center justify-center gap-2 rounded-lg border border-slate-100 bg-slate-50 text-[#55799a] text-[10px] font-black uppercase tracking-widest hover:bg-white transition-all"
              >
                <UploadCloud className="w-3.5 h-3.5" />
                {videoFileName ? 'Replace Video' : 'Choose Video'}
              </button>
              <div className="h-5 truncate text-[10px] font-mono text-slate-400">
                {videoFileName || 'No video selected'}
              </div>
            </div>
          )}
        </div>

      </div>

    </main>
  );
}

export default function Home() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="w-10 h-10 border-4 border-[#55799a] border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <HomeContent />
    </Suspense>
  );
}
