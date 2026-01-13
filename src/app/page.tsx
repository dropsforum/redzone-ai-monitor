"use client";

import React, { useState, useEffect, useRef, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Play, Square, Edit3, RefreshCcw, Camera, Settings, Zap, Cpu, Volume2, VolumeX, Smartphone, Monitor } from 'lucide-react';
import WebcamCapture, { WebcamCaptureHandle } from '../components/WebcamCapture';
import ZoneEditor, { Point } from '../components/ZoneEditor';
import DetectionOverlay from '../components/DetectionOverlay';
import TrafficLight, { TrafficLightState } from '../components/TrafficLight';
import { YoloDetector, Detection } from '../lib/yolo-detector';
import { isPersonInZone, isPersonNearZone } from '../lib/zone-checker';
import { AlertManager } from '../lib/alert-manager';

function HomeContent() {
  // App State
  const searchParams = useSearchParams();
  const isEmbedMode = searchParams.get('embed') === 'true';
  
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isModelLoaded, setIsModelLoaded] = useState(false);
  const [isAudioEnabled, setIsAudioEnabled] = useState(true);
  const [isMobileMode, setIsMobileMode] = useState(false);
  const [fps, setFps] = useState(0);
  
  // Data State
  const [detections, setDetections] = useState<Detection[]>([]);
  const [zone, setZone] = useState<Point[]>([]);
  const [alertActive, setAlertActive] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [trafficLightState, setTrafficLightState] = useState<TrafficLightState>('green');
  
  // Camera State
  const [availableDevices, setAvailableDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null);
  
  // Detection Settings
  const [warningBuffer, setWarningBuffer] = useState(0.1); // normalized distance 0.0 - 0.3

  // Refs
  const detectorRef = useRef<YoloDetector | null>(null);
  const alertManagerRef = useRef<AlertManager>(new AlertManager(5));
  const webcamRef = useRef<WebcamCaptureHandle>(null);
  const lastProcessedTimeRef = useRef<number>(0);
  const frameCountRef = useRef<number>(0);
  const lastFpsUpdateRef = useRef<number>(0);

  // Screenshot Logic
  const captureScreenshot = useCallback(() => {
    if (!webcamRef.current || !dimensions.width) return;

    const video = webcamRef.current.getVideo();
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
    // Initial scan
    getDevices();
    
    // Re-scan after a short delay to catch Continuity Cameras/iPhone
    const timer = setTimeout(() => getDevices(), 2000);
    
    // Listen for hardware changes
    navigator.mediaDevices.addEventListener('devicechange', () => getDevices());
    
    return () => {
      clearTimeout(timer);
      navigator.mediaDevices.removeEventListener('devicechange', () => getDevices());
    };
  }, [getDevices]);

  // Initialize Detector
  useEffect(() => {
    const init = async () => {
      const detector = new YoloDetector();
      await detector.init('/models/yolo11n.onnx');
      detectorRef.current = detector;
      setIsModelLoaded(true);
    };
    init();

    // Check if mobile
    setIsMobileMode(/iPhone|iPad|iPod|Android/i.test(navigator.userAgent));
  }, []);

  // Reset traffic light when not monitoring
  useEffect(() => {
    if (!isMonitoring) {
      setTrafficLightState('green');
    }
  }, [isMonitoring]);

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
        
        // Check for zone alerts
        if (zone.length >= 3 && results.length > 0) {
          const personInZone = results.some(det => {
            const inZone = isPersonInZone(det, zone, canvas.width, canvas.height, true);
            return inZone;
          });

          if (personInZone) {
            setAlertActive(true);
            setTrafficLightState('red');
            alertManagerRef.current.trigger(isAudioEnabled).catch(e => console.error('[APP] Alert trigger failed:', e));
          } else {
            setAlertActive(false);
            // Yellow: person is near or partially in zone
            const personNearZone = results.some(det => isPersonNearZone(det, zone, canvas.width, canvas.height, warningBuffer));
            setTrafficLightState(personNearZone ? 'yellow' : 'green');
          }
        } else {
          // Green: no zone or no detections
          setTrafficLightState('green');
        }

        // FPS Calculation
        frameCountRef.current++;
        if (now - lastFpsUpdateRef.current >= 1000) {
          setFps(frameCountRef.current);
          frameCountRef.current = 0;
          lastFpsUpdateRef.current = now;
        }
      });
    }
  }, [isMonitoring, isModelLoaded, zone, isAudioEnabled, isMobileMode, dimensions]);

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
              <span className="text-[10px] font-bold uppercase text-slate-600">{isModelLoaded ? 'AI Ready' : 'Loading...'}</span>
            </div>
          </div>
          <p className="text-slate-400 text-[10px] font-mono flex items-center gap-2 uppercase tracking-widest">
            <Zap className="w-3 h-3 text-[#55799a]" /> POWERED BY YOLOv11 AI • BROWSER-NATIVE
          </p>
        </div>
      )}

      <div className="space-y-6">
        {/* Monitoring Panel */}
        <div className="space-y-4">
          <div className="relative aspect-video bg-slate-50 rounded-xl overflow-hidden border border-slate-200 shadow-sm ring-1 ring-slate-100">
            {/* Components Layered */}
            <WebcamCapture 
              ref={webcamRef} 
              onFrame={handleFrame}
              width={isMobileMode ? 640 : 1280}
              height={isMobileMode ? 480 : 720}
              deviceId={selectedDeviceId}
            />
            
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
            
            {isMonitoring && <TrafficLight state={trafficLightState} />}

            {/* Empty State / Loading */}
            {!isModelLoaded && (
              <div className="absolute inset-0 bg-white/90 backdrop-blur-sm z-[60] flex flex-col items-center justify-center">
                <div className="w-10 h-10 border-4 border-[#55799a] border-t-transparent rounded-full animate-spin mb-4" />
                <p className="text-[#55799a] font-black tracking-widest uppercase text-xs">Initializing AI</p>
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
              onClick={() => {
                alertManagerRef.current.unlockAudio();
                setIsMonitoring(!isMonitoring);
              }}
              disabled={!isModelLoaded || zone.length < 3}
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
                if (!isDrawing) setIsMonitoring(false);
              }}
              className={`flex-1 min-w-[140px] h-12 flex items-center justify-center gap-2 rounded-xl font-bold transition-all border-2 ${
                isDrawing 
                ? `bg-red-50 border-red-500 text-red-500 ${zone.length >= 3 ? 'animate-subtle-blink border-red-600 shadow-md' : ''}` 
                : `bg-white border-[#55799a] text-[#55799a] hover:bg-slate-50 shadow-sm ${zone.length === 0 ? 'animate-subtle-blink shadow-[#55799a]/20' : ''}`
              }`}
            >
              <Edit3 className="w-4 h-4" />
              <span className="uppercase text-[10px] tracking-widest">{isDrawing ? 'Save Zone' : 'Draw Zone'}</span>
            </button>
            
            <button
              onClick={captureScreenshot}
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
