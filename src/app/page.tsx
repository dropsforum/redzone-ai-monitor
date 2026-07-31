"use client";

import React, { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Play, Square, Edit3, RefreshCcw, Camera, Settings, Zap, Cpu, Volume2, VolumeX, Smartphone, Monitor, Video, UploadCloud, BarChart3, Download, Users } from 'lucide-react';
import VideoFrameSource, { VideoFrameRect, VideoFrameSourceHandle, VideoSourceMode } from '../components/VideoFrameSource';
import ZoneEditor, { Point } from '../components/ZoneEditor';
import DetectionOverlay from '../components/DetectionOverlay';
import TrafficLight, { TrafficLightState } from '../components/TrafficLight';
import {
  YoloDetector,
  type BrowserInferenceBackend,
  type InferenceResult,
} from '../lib/yolo-detector';
import { AlertManager } from '../lib/alert-manager';
import {
  BreachAggregateMode,
  BreachRecorder,
  BreachSnapshot,
  formatBucketLabel,
  formatDuration,
  summarizeBreachSegments,
} from '../lib/breach-recorder';
import {
  BrowserSessionStore,
  createMonitoringSession,
  type InferenceHealth,
  type MonitoringSessionArchive,
} from '../lib/session-store';
import {
  ZoneMonitor,
  type PersonBreachEvent,
  type TrackedDetection,
} from '../lib/zone-monitor';

type BreachReportTab = 'records' | 'people' | 'metrics';

interface MutableInferenceHealth {
  samples: number;
  preprocessTotalMs: number;
  inferenceTotalMs: number;
  postprocessTotalMs: number;
  maxInferenceMs: number;
  droppedInferenceRequests: number;
  detectorErrors: number;
}

function emptyMutableHealth(): MutableInferenceHealth {
  return {
    samples: 0,
    preprocessTotalMs: 0,
    inferenceTotalMs: 0,
    postprocessTotalMs: 0,
    maxInferenceMs: 0,
    droppedInferenceRequests: 0,
    detectorErrors: 0,
  };
}

function summarizeHealth(health: MutableInferenceHealth, observedFps: number): InferenceHealth {
  const divisor = Math.max(1, health.samples);
  return {
    observedFps,
    inferenceSamples: health.samples,
    averagePreprocessMs: health.preprocessTotalMs / divisor,
    averageInferenceMs: health.inferenceTotalMs / divisor,
    averagePostprocessMs: health.postprocessTotalMs / divisor,
    maxInferenceMs: health.maxInferenceMs,
    droppedInferenceRequests: health.droppedInferenceRequests,
    detectorErrors: health.detectorErrors,
  };
}

function hasVideoSource(
  sourceMode: VideoSourceMode,
  videoUrl: string | null,
  dimensions: { width: number; height: number },
) {
  return Boolean(dimensions.width && dimensions.height && (sourceMode === 'camera' || videoUrl));
}

function HomeContent() {
  // App State
  const searchParams = useSearchParams();
  const isEmbedMode = searchParams.get('embed') === 'true';
  const requestedBackend = searchParams.get('backend') === 'litert' ? 'litert' : 'onnx';
  
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isModelLoaded, setIsModelLoaded] = useState(false);
  const [modelError, setModelError] = useState<string | null>(null);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [isMobileMode] = useState(() => (
    typeof navigator !== 'undefined' && /iPhone|iPad|iPod|Android/i.test(navigator.userAgent)
  ));
  const [fps, setFps] = useState(0);
  const [inferenceLatencyMs, setInferenceLatencyMs] = useState(0);
  const [activeBackend, setActiveBackend] = useState('onnx-wasm');
  const [sourceMode, setSourceMode] = useState<VideoSourceMode>('camera');
  
  // Data State
  const [detections, setDetections] = useState<TrackedDetection[]>([]);
  const [zone, setZone] = useState<Point[]>([]);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [trafficLightState, setTrafficLightState] = useState<TrafficLightState>('green');
  const [personEvents, setPersonEvents] = useState<PersonBreachEvent[]>([]);
  const [savedSessions, setSavedSessions] = useState<MonitoringSessionArchive[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState('');
  const [currentSessionArchive, setCurrentSessionArchive] = useState<MonitoringSessionArchive | null>(null);
  const [liveHealth, setLiveHealth] = useState<InferenceHealth>(() => summarizeHealth(emptyMutableHealth(), 0));
  
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
  const detectorRef = useRef<BrowserInferenceBackend | null>(null);
  const alertManagerRef = useRef<AlertManager>(new AlertManager(5));
  const breachRecorderRef = useRef<BreachRecorder>(new BreachRecorder());
  const zoneMonitorRef = useRef<ZoneMonitor>(new ZoneMonitor());
  const sessionStoreRef = useRef<BrowserSessionStore | null>(null);
  const currentArchiveRef = useRef<MonitoringSessionArchive | null>(null);
  const personEventHistoryRef = useRef<PersonBreachEvent[]>([]);
  const personEventsRef = useRef<PersonBreachEvent[]>([]);
  const healthRef = useRef<MutableInferenceHealth>(emptyMutableHealth());
  const fpsRef = useRef(0);
  const monitoringGenerationRef = useRef(0);
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

  const replacePersonEvents = useCallback((events: PersonBreachEvent[]) => {
    personEventsRef.current = events;
    setPersonEvents(events);
  }, []);

  const persistCurrentSession = useCallback(async (
    nowMs = Date.now(),
    status?: 'completed' | 'interrupted',
  ) => {
    const archive = currentArchiveRef.current;
    const store = sessionStoreRef.current;
    if (!archive || !store) return;

    archive.session.lastHeartbeatMs = nowMs;
    if (status) {
      archive.session.status = status;
      archive.session.endedAtMs = nowMs;
    }
    archive.segments = breachRecorderRef.current.snapshot(breachAggregateMode, nowMs).segments;
    archive.personEvents = personEventsRef.current.map(event => ({ ...event }));
    archive.health = summarizeHealth(healthRef.current, fpsRef.current);
    await store.save(archive);
    if (currentArchiveRef.current?.session.id === archive.session.id) {
      setCurrentSessionArchive(structuredClone(archive));
    }
    setSavedSessions(await store.list());
  }, [breachAggregateMode]);

  const closeActiveTracks = useCallback((nowMs: number, resetTrackIds: boolean) => {
    const stopped = zoneMonitorRef.current.stop(nowMs);
    const merged = [
      ...personEventHistoryRef.current,
      ...stopped.personEvents,
    ];
    personEventHistoryRef.current = merged;
    replacePersonEvents(merged);
    zoneMonitorRef.current.reset(resetTrackIds);
  }, [replacePersonEvents]);

  const completeMonitoringSession = useCallback(async (nowMs = Date.now()) => {
    monitoringGenerationRef.current += 1;
    if (currentArchiveRef.current?.session.status !== 'active') return;
    closeActiveTracks(nowMs, true);
    breachRecorderRef.current.stop(nowMs);
    setTrafficLightState('green');
    setDetections([]);
    refreshBreachSnapshot();
    await persistCurrentSession(nowMs, 'completed');
  }, [closeActiveTracks, persistCurrentSession, refreshBreachSnapshot]);

  const resetRuntimeState = useCallback(() => {
    if (currentArchiveRef.current?.session.status === 'active') {
      void completeMonitoringSession(Date.now());
    }
    setIsMonitoring(false);
    setDetections([]);
    setTrafficLightState('green');
    setDimensions({ width: 0, height: 0 });
    setFrameRect({ left: 0, top: 0, width: 0, height: 0 });
    setFps(0);
    setInferenceLatencyMs(0);
    frameCountRef.current = 0;
    fpsRef.current = 0;
    lastProcessedTimeRef.current = 0;
    lastFpsUpdateRef.current = 0;
    breachRecorderRef.current.reset();
    zoneMonitorRef.current.reset();
    personEventHistoryRef.current = [];
    replacePersonEvents([]);
    healthRef.current = emptyMutableHealth();
    currentArchiveRef.current = null;
    setCurrentSessionArchive(null);
    setLiveHealth(summarizeHealth(emptyMutableHealth(), 0));
    setSelectedSessionId('');
    setBreachSnapshot(breachRecorderRef.current.snapshot(breachAggregateMode));
  }, [breachAggregateMode, completeMonitoringSession, replacePersonEvents]);

  useEffect(() => {
    const store = new BrowserSessionStore();
    sessionStoreRef.current = store;
    void store.recoverInterruptedSessions().then(() => store.list()).then(setSavedSessions).catch(error => {
      console.error('[SESSION] Failed to load monitoring history:', error);
    });
  }, []);

  useEffect(() => {
    refreshBreachSnapshot();
  }, [refreshBreachSnapshot]);

  useEffect(() => {
    if (!isMonitoring) return;
    const timer = window.setInterval(refreshBreachSnapshot, 1000);
    return () => window.clearInterval(timer);
  }, [isMonitoring, refreshBreachSnapshot]);

  useEffect(() => {
    if (!isMonitoring) return;
    const timer = window.setInterval(() => {
      void persistCurrentSession(Date.now()).catch(error => {
        console.error('[SESSION] Heartbeat failed:', error);
      });
    }, 5000);
    return () => window.clearInterval(timer);
  }, [isMonitoring, persistCurrentSession]);

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

  const selectedArchive = selectedSessionId
    ? savedSessions.find(archive => archive.session.id === selectedSessionId) ?? null
    : null;
  const displayedBreachSnapshot = selectedArchive
    ? summarizeBreachSegments(selectedArchive.segments, breachAggregateMode)
    : breachSnapshot;
  const displayedPersonEvents = selectedArchive?.personEvents ?? personEvents;
  const displayedHealth = selectedArchive?.health
    ?? liveHealth;

  const exportSessionWorkbook = useCallback(async () => {
    let archive = selectedSessionId
      ? savedSessions.find(saved => saved.session.id === selectedSessionId) ?? null
      : null;
    if (!archive && currentArchiveRef.current) {
      const nowMs = Date.now();
      const current = currentArchiveRef.current;
      current.segments = breachRecorderRef.current.snapshot(breachAggregateMode, nowMs).segments;
      current.personEvents = personEventsRef.current.map(event => ({ ...event }));
      current.health = summarizeHealth(healthRef.current, fpsRef.current);
      archive = structuredClone(current);
    }
    if (!archive) return;

    const { buildSessionWorkbook } = await import('../lib/report-workbook');
    const workbook = await buildSessionWorkbook(archive, breachAggregateMode);
    const workbookBuffer = new ArrayBuffer(workbook.byteLength);
    new Uint8Array(workbookBuffer).set(workbook);
    const blob = new Blob([workbookBuffer], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `drops-red-zone-session-${archive.session.id}.xlsx`;
    link.click();
    URL.revokeObjectURL(url);
  }, [breachAggregateMode, savedSessions, selectedSessionId]);

  useEffect(() => {
    return () => {
      if (videoObjectUrlRef.current) URL.revokeObjectURL(videoObjectUrlRef.current);
      detectorRef.current?.dispose();
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
      const label = `PERSON #${det.trackId} ${Math.round(det.confidence * 100)}%`;
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
    let cancelled = false;
    let initializedDetector: BrowserInferenceBackend | null = null;
    const init = async () => {
      try {
        const detector: BrowserInferenceBackend = requestedBackend === 'litert'
          ? new (await import('../lib/litert-detector')).LiteRtDetector()
          : new YoloDetector();
        initializedDetector = detector;
        const modelPath = requestedBackend === 'litert'
          ? '/models/yolo26n.tflite'
          : '/models/yolo26n.onnx';
        await detector.init(modelPath);
        if (cancelled) {
          detector.dispose();
          return;
        }
        detectorRef.current = detector;
        setActiveBackend(detector.backend);
        setIsModelLoaded(true);
        setModelError(null);
      } catch (error) {
        console.error('[APP] Failed to initialize detector:', error);
        const message = error instanceof Error ? error.message : String(error);
        setModelError(
          /404|fetch|not found/i.test(message)
            ? `Generate public/models/yolo26n.${requestedBackend === 'litert' ? 'tflite' : 'onnx'} before monitoring.`
            : `The YOLO26 model could not be initialized: ${message}`,
        );
      }
    };
    void init();
    return () => {
      cancelled = true;
      if (detectorRef.current === initializedDetector) detectorRef.current = null;
      initializedDetector?.dispose();
    };
  }, [requestedBackend]);

  const startMonitoring = useCallback(async () => {
    if (!isModelLoaded || zone.length < 3 || !hasVideoSource(sourceMode, videoUrl, dimensions)) return;
    monitoringGenerationRef.current += 1;
    await alertManagerRef.current.unlockAudio();
    setIsDrawing(false);
    setSelectedSessionId('');
    zoneMonitorRef.current.reset();
    zoneMonitorRef.current.setWarningBuffer(warningBuffer);
    personEventHistoryRef.current = [];
    replacePersonEvents([]);
    healthRef.current = emptyMutableHealth();
    breachRecorderRef.current.reset();

    const nowMs = Date.now();
    breachRecorderRef.current.start(nowMs);
    const sourceLabel = sourceMode === 'file'
      ? videoFileName ?? 'Recorded video'
      : availableDevices.find(device => device.deviceId === selectedDeviceId)?.label || 'Camera';
    currentArchiveRef.current = {
      session: createMonitoringSession({
        startedAtMs: nowMs,
        sourceMode,
        sourceLabel,
        zone,
        modelName: 'yolo26n',
        modelVersion: '8.4.112',
        backend: detectorRef.current?.backend ?? activeBackend,
        warningBuffer,
      }),
      segments: [],
      personEvents: [],
      health: summarizeHealth(healthRef.current, 0),
    };
    setCurrentSessionArchive(structuredClone(currentArchiveRef.current));
    setLiveHealth(summarizeHealth(healthRef.current, 0));
    setIsMonitoring(true);
    if (sourceMode === 'file') {
      await videoSourceRef.current?.play().catch(error => {
        console.error('[APP] Recorded video playback failed:', error);
      });
    }
    await persistCurrentSession(nowMs).catch(error => {
      console.error('[SESSION] Initial save failed:', error);
    });
  }, [
    activeBackend,
    availableDevices,
    dimensions,
    isModelLoaded,
    persistCurrentSession,
    replacePersonEvents,
    selectedDeviceId,
    sourceMode,
    videoFileName,
    videoUrl,
    warningBuffer,
    zone,
  ]);

  const stopMonitoring = useCallback(async () => {
    const nowMs = Date.now();
    setIsMonitoring(false);
    if (sourceMode === 'file') videoSourceRef.current?.pause();
    await completeMonitoringSession(nowMs).catch(error => {
      console.error('[SESSION] Final save failed:', error);
    });
  }, [completeMonitoringSession, sourceMode]);

  const handleTimelineReset = useCallback(() => {
    if (!isMonitoring) return;
    monitoringGenerationRef.current += 1;
    const nowMs = Date.now();
    closeActiveTracks(nowMs, false);
    breachRecorderRef.current.update(false, nowMs);
    setTrafficLightState('green');
    setDetections([]);
    refreshBreachSnapshot();
    void persistCurrentSession(nowMs).catch(error => {
      console.error('[SESSION] Timeline reset save failed:', error);
    });
  }, [closeActiveTracks, isMonitoring, persistCurrentSession, refreshBreachSnapshot]);

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
      const monitoringGeneration = monitoringGenerationRef.current;
      
      detectorRef.current.detect(canvas).then((result: InferenceResult) => {
        if (
          monitoringGeneration !== monitoringGenerationRef.current
          || currentArchiveRef.current?.session.status !== 'active'
        ) {
          return;
        }
        if (result.dropped) {
          healthRef.current.droppedInferenceRequests += 1;
          return;
        }

        const resultTime = Date.now();
        healthRef.current.samples += 1;
        healthRef.current.preprocessTotalMs += result.timings.preprocessMs;
        healthRef.current.inferenceTotalMs += result.timings.inferenceMs;
        healthRef.current.postprocessTotalMs += result.timings.postprocessMs;
        healthRef.current.maxInferenceMs = Math.max(
          healthRef.current.maxInferenceMs,
          result.timings.inferenceMs,
        );
        setLiveHealth(summarizeHealth(healthRef.current, fpsRef.current));
        setInferenceLatencyMs(result.timings.totalMs);
        setActiveBackend(result.backend);

        zoneMonitorRef.current.setWarningBuffer(warningBuffer);
        const zoneSnapshot = zoneMonitorRef.current.update(
          result.detections,
          zone,
          canvas.width,
          canvas.height,
          resultTime,
        );
        setDetections(zoneSnapshot.tracks);
        setTrafficLightState(zoneSnapshot.state);
        replacePersonEvents([
          ...personEventHistoryRef.current,
          ...zoneSnapshot.personEvents,
        ]);

        if (zoneSnapshot.enteredRed) {
          alertManagerRef.current.trigger(isAudioEnabled).catch(error => {
            console.error('[APP] Alert trigger failed:', error);
          });
        }

        breachRecorderRef.current.update(
          zoneSnapshot.state === 'red',
          zoneSnapshot.stateChangedAtMs ?? resultTime,
        );
        refreshBreachSnapshot();
        if (zoneSnapshot.stateChangedAtMs !== null) {
          void persistCurrentSession(resultTime).catch(error => {
            console.error('[SESSION] State transition save failed:', error);
          });
        }

        // FPS Calculation
        frameCountRef.current++;
        if (resultTime - lastFpsUpdateRef.current >= 1000) {
          setFps(frameCountRef.current);
          fpsRef.current = frameCountRef.current;
          setLiveHealth(summarizeHealth(healthRef.current, fpsRef.current));
          frameCountRef.current = 0;
          lastFpsUpdateRef.current = resultTime;
        }
      }).catch(error => {
        if (monitoringGeneration !== monitoringGenerationRef.current) return;
        healthRef.current.detectorErrors += 1;
        console.error('[APP] Detection failed:', error);
      });
    }
  }, [
    dimensions,
    isAudioEnabled,
    isMobileMode,
    isModelLoaded,
    isMonitoring,
    persistCurrentSession,
    refreshBreachSnapshot,
    replacePersonEvents,
    warningBuffer,
    zone,
  ]);

  const overlayStyle: React.CSSProperties = {
    left: frameRect.left,
    top: frameRect.top,
    width: frameRect.width || '100%',
    height: frameRect.height || '100%',
  };
  const hasActiveVideoSource = hasVideoSource(sourceMode, videoUrl, dimensions);

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
              onTimelineReset={handleTimelineReset}
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
              <div className="flex items-center gap-2 text-slate-400">
                <Cpu className="w-3 h-3" />
                <span className="text-[10px] font-mono font-bold">
                  {activeBackend} · {Math.round(inferenceLatencyMs)} ms
                </span>
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
              onClick={() => {
                void (isMonitoring ? stopMonitoring() : startMonitoring());
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
                  if (isMonitoring) void stopMonitoring();
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
              <select
                value={selectedSessionId}
                onChange={(event) => setSelectedSessionId(event.target.value)}
                className="h-8 max-w-[210px] rounded-lg border border-slate-100 bg-slate-50 px-2 text-[9px] font-mono text-slate-500 outline-none"
                title="Monitoring session"
              >
                <option value="">Current session</option>
                {savedSessions.map(archive => (
                  <option key={archive.session.id} value={archive.session.id}>
                    {new Date(archive.session.startedAtMs).toLocaleString()} · {archive.session.sourceLabel}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => {
                  void (async () => {
                    if (isMonitoring) {
                      await completeMonitoringSession(Date.now());
                      currentArchiveRef.current = null;
                      setCurrentSessionArchive(null);
                      await startMonitoring();
                      return;
                    }
                    breachRecorderRef.current.reset();
                    zoneMonitorRef.current.reset();
                    personEventHistoryRef.current = [];
                    replacePersonEvents([]);
                    currentArchiveRef.current = null;
                    setCurrentSessionArchive(null);
                    setSelectedSessionId('');
                    setBreachSnapshot(breachRecorderRef.current.snapshot(breachAggregateMode));
                  })();
                }}
                className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-slate-100 text-[#55799a] hover:bg-slate-50"
                title="Reset breach recording"
              >
                <RefreshCcw className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => void exportSessionWorkbook()}
                disabled={!selectedArchive && !currentSessionArchive}
                className="h-8 w-8 inline-flex items-center justify-center rounded-lg border border-slate-100 text-[#55799a] hover:bg-slate-50 disabled:opacity-40"
                title="Export session Excel workbook"
              >
                <Download className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1 shadow-sm">
            {(['records', 'people', 'metrics'] as BreachReportTab[]).map((tab) => (
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
                  <div className="text-lg font-black text-red-500">{displayedBreachSnapshot.breachCount}</div>
                </div>
                <div className="rounded-xl bg-green-50 border border-green-100 p-3">
                  <div className="text-[8px] uppercase tracking-widest font-black text-green-400">No-Breach Records</div>
                  <div className="text-lg font-black text-green-600">{displayedBreachSnapshot.clearCount}</div>
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
                    {displayedBreachSnapshot.segments.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-3 py-8 text-center uppercase tracking-widest text-slate-300 font-black">
                          Start monitoring to record breach and no-breach periods
                        </td>
                      </tr>
                    ) : (
                      displayedBreachSnapshot.segments.slice(-20).map((segment, index) => (
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
          ) : breachReportTab === 'people' ? (
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-2">
                <div className="rounded-xl border border-red-100 bg-red-50 p-3">
                  <div className="text-[8px] font-black uppercase tracking-widest text-red-300">Person Breaches</div>
                  <div className="text-lg font-black text-red-500">{displayedPersonEvents.length}</div>
                </div>
                <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                  <div className="text-[8px] font-black uppercase tracking-widest text-slate-400">Tracked People</div>
                  <div className="text-lg font-black text-[#55799a]">
                    {new Set(displayedPersonEvents.map(event => event.trackId)).size}
                  </div>
                </div>
                <div className="rounded-xl border border-slate-100 bg-slate-50 p-3">
                  <div className="text-[8px] font-black uppercase tracking-widest text-slate-400">Combined Time</div>
                  <div className="text-lg font-black text-slate-700">
                    {formatDuration(displayedPersonEvents.reduce((sum, event) => sum + event.endMs - event.startMs, 0))}
                  </div>
                </div>
              </div>

              <div className="max-h-64 overflow-auto rounded-xl border border-slate-100">
                <table className="w-full text-left text-[9px]">
                  <thead className="sticky top-0 bg-slate-50 uppercase tracking-widest text-slate-400">
                    <tr>
                      <th className="px-3 py-2">Person</th>
                      <th className="px-3 py-2">Start</th>
                      <th className="px-3 py-2">End</th>
                      <th className="px-3 py-2 text-right">Duration</th>
                      <th className="px-3 py-2 text-right">Max confidence</th>
                    </tr>
                  </thead>
                  <tbody className="font-mono text-slate-500">
                    {displayedPersonEvents.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-3 py-8 text-center font-black uppercase tracking-widest text-slate-300">
                          No confirmed person breaches
                        </td>
                      </tr>
                    ) : (
                      displayedPersonEvents.slice(-100).map((event, index) => (
                        <tr key={`${event.trackId}-${event.startMs}-${index}`} className="border-t border-slate-100">
                          <td className="px-3 py-2 font-black text-[#55799a]">
                            <span className="inline-flex items-center gap-1">
                              <Users className="h-3 w-3" /> #{event.trackId}
                            </span>
                          </td>
                          <td className="px-3 py-2">{new Date(event.startMs).toLocaleString()}</td>
                          <td className="px-3 py-2">{new Date(event.endMs).toLocaleString()}</td>
                          <td className="px-3 py-2 text-right">{formatDuration(event.endMs - event.startMs)}</td>
                          <td className="px-3 py-2 text-right">{Math.round(event.maxConfidence * 100)}%</td>
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
                  <div className="text-lg font-black text-red-500">{formatDuration(displayedBreachSnapshot.totalBreachMs)}</div>
                </div>
                <div className="rounded-xl bg-slate-50 border border-slate-100 p-3">
                  <div className="text-[8px] uppercase tracking-widest font-black text-slate-400">Rate</div>
                  <div className="text-lg font-black text-[#55799a]">
                    {displayedBreachSnapshot.totalMs > 0 ? `${Math.round((displayedBreachSnapshot.totalBreachMs / displayedBreachSnapshot.totalMs) * 100)}%` : '0%'}
                  </div>
                </div>
                <div className="rounded-xl bg-slate-50 border border-slate-100 p-3">
                  <div className="text-[8px] uppercase tracking-widest font-black text-slate-400">Observed</div>
                  <div className="text-lg font-black text-slate-700">{formatDuration(displayedBreachSnapshot.totalMs)}</div>
                </div>
              </div>

              <div className="h-32 rounded-xl border border-slate-100 bg-slate-50 px-3 pt-3 pb-7">
                {displayedBreachSnapshot.buckets.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-[10px] uppercase tracking-widest font-black text-slate-300">
                    Start monitoring to produce metrics
                  </div>
                ) : (
                  <div className="h-full flex items-end gap-1">
                    {displayedBreachSnapshot.buckets.slice(-18).map((bucket) => (
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
                      {displayedBreachSnapshot.buckets.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="px-3 py-8 text-center uppercase tracking-widest text-slate-300 font-black">
                            No aggregated report yet
                          </td>
                        </tr>
                      ) : (
                        displayedBreachSnapshot.buckets.slice(-60).map((bucket) => (
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

              <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
                {[
                  ['Preprocess', `${displayedHealth.averagePreprocessMs.toFixed(1)} ms`],
                  ['Inference', `${displayedHealth.averageInferenceMs.toFixed(1)} ms`],
                  ['Postprocess', `${displayedHealth.averagePostprocessMs.toFixed(1)} ms`],
                  ['Dropped / errors', `${displayedHealth.droppedInferenceRequests} / ${displayedHealth.detectorErrors}`],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2">
                    <div className="text-[7px] font-black uppercase tracking-widest text-slate-400">{label}</div>
                    <div className="mt-1 text-[10px] font-mono font-bold text-slate-600">{value}</div>
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-2 text-[9px] font-mono text-slate-400">
                <span className="px-2 py-1 rounded-lg border border-slate-100 bg-slate-50">
                  Period start: {displayedBreachSnapshot.periodStartMs ? new Date(displayedBreachSnapshot.periodStartMs).toLocaleString() : 'None'}
                </span>
                <span className="px-2 py-1 rounded-lg border border-slate-100 bg-slate-50">
                  Period end: {displayedBreachSnapshot.periodEndMs ? new Date(displayedBreachSnapshot.periodEndMs).toLocaleString() : 'None'}
                </span>
                <span className={`px-2 py-1 rounded-lg border ${displayedBreachSnapshot.currentState === 'breach' ? 'bg-red-50 text-red-500 border-red-100' : 'bg-green-50 text-green-600 border-green-100'}`}>
                  Current: {displayedBreachSnapshot.currentState === 'breach' ? `Breach ${formatDuration(displayedBreachSnapshot.activeBreachMs)}` : 'Clear'}
                </span>
                <span className="px-2 py-1 rounded-lg border border-slate-100 bg-slate-50">
                  Clear: {formatDuration(displayedBreachSnapshot.totalClearMs)}
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
              onChange={(e) => {
                const nextBuffer = parseFloat(e.target.value);
                setWarningBuffer(nextBuffer);
                zoneMonitorRef.current.setWarningBuffer(nextBuffer);
                if (currentArchiveRef.current?.session.status === 'active') {
                  currentArchiveRef.current.session.warningBuffer = nextBuffer;
                }
              }}
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
                onChange={(e) => {
                  if (isMonitoring) void stopMonitoring();
                  zoneMonitorRef.current.reset();
                  setSelectedDeviceId(e.target.value);
                }}
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
