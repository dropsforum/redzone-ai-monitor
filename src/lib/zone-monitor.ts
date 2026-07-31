import type { Point } from '../components/ZoneEditor';
import type { Detection } from './yolo-detector';
import { distanceToZoneEdge, isPointInPolygon } from './zone-checker';

export type ZoneMonitorState = 'green' | 'yellow' | 'red';

export interface ZoneMonitorConfig {
  entryConfirmMs: number;
  exitGraceMs: number;
  trackerMaxGapMs: number;
  matchIouThreshold: number;
  matchDistanceRatio: number;
  warningBuffer: number;
}

export interface PersonBreachEvent {
  trackId: number;
  startMs: number;
  endMs: number;
  maxConfidence: number;
}

export interface TrackedDetection extends Detection {
  trackId: number;
  insideZone: boolean;
  pendingEntry: boolean;
  breachActive: boolean;
  footPoint: Point;
}

export interface ZoneMonitorSnapshot {
  state: ZoneMonitorState;
  enteredRed: boolean;
  stateChangedAtMs: number | null;
  tracks: TrackedDetection[];
  activeBreachTrackIds: number[];
  personEvents: PersonBreachEvent[];
}

interface Track {
  id: number;
  detection: Detection;
  firstSeenMs: number;
  lastSeenMs: number;
  insideSinceMs: number | null;
  lastInsideMs: number | null;
  breachStartMs: number | null;
  maxConfidence: number;
  insideZone: boolean;
  nearZone: boolean;
  footPoint: Point;
}

const DEFAULT_CONFIG: ZoneMonitorConfig = {
  entryConfirmMs: 300,
  exitGraceMs: 750,
  trackerMaxGapMs: 750,
  matchIouThreshold: 0.3,
  matchDistanceRatio: 0.08,
  warningBuffer: 0.1,
};

export class ZoneMonitor {
  private config: ZoneMonitorConfig;
  private tracks = new Map<number, Track>();
  private completedEvents: PersonBreachEvent[] = [];
  private nextTrackId = 1;
  private state: ZoneMonitorState = 'green';

  constructor(config: Partial<ZoneMonitorConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  setWarningBuffer(warningBuffer: number) {
    this.config.warningBuffer = warningBuffer;
  }

  update(
    detections: Detection[],
    zone: Point[],
    imageWidth: number,
    imageHeight: number,
    nowMs = Date.now(),
  ): ZoneMonitorSnapshot {
    if (imageWidth <= 0 || imageHeight <= 0 || zone.length < 3) {
      return this.finishUpdate([], nowMs);
    }

    const matches = this.matchDetections(detections, imageWidth, imageHeight, nowMs);
    const currentTracks: Track[] = [];

    for (const { detection, track } of matches) {
      const footPoint = detectionFootPoint(detection, imageWidth, imageHeight);
      const insideZone = isPointInPolygon(footPoint, zone);
      const nearZone = !insideZone && distanceToZoneEdge(footPoint, zone) <= this.config.warningBuffer;

      track.detection = detection;
      track.lastSeenMs = nowMs;
      track.maxConfidence = Math.max(track.maxConfidence, detection.confidence);
      track.insideZone = insideZone;
      track.nearZone = nearZone;
      track.footPoint = footPoint;

      if (insideZone) {
        track.insideSinceMs ??= nowMs;
        track.lastInsideMs = nowMs;
        if (
          track.breachStartMs === null
          && nowMs - track.insideSinceMs >= this.config.entryConfirmMs
        ) {
          track.breachStartMs = track.insideSinceMs;
        }
      } else if (track.breachStartMs === null) {
        track.insideSinceMs = null;
      }

      currentTracks.push(track);
    }

    return this.finishUpdate(currentTracks, nowMs);
  }

  stop(nowMs = Date.now()): ZoneMonitorSnapshot {
    const previousState = this.state;
    for (const track of this.tracks.values()) {
      this.closeEvent(track, nowMs);
    }
    this.tracks.clear();
    this.state = 'green';
    return {
      state: 'green',
      enteredRed: false,
      stateChangedAtMs: previousState === 'green' ? null : nowMs,
      tracks: [],
      activeBreachTrackIds: [],
      personEvents: [...this.completedEvents],
    };
  }

  reset(resetTrackIds = true) {
    this.tracks.clear();
    this.completedEvents = [];
    if (resetTrackIds) this.nextTrackId = 1;
    this.state = 'green';
  }

  private finishUpdate(currentTracks: Track[], nowMs: number): ZoneMonitorSnapshot {
    const endedAtMs: number[] = [];
    for (const track of [...this.tracks.values()]) {
      if (
        track.breachStartMs !== null
        && track.lastInsideMs !== null
        && nowMs - track.lastInsideMs > this.config.exitGraceMs
      ) {
        const eventEndMs = this.closeEvent(
          track,
          track.lastInsideMs + this.config.exitGraceMs,
        );
        if (eventEndMs !== null) endedAtMs.push(eventEndMs);
      }

      if (nowMs - track.lastSeenMs > this.config.trackerMaxGapMs) {
        this.tracks.delete(track.id);
      }
    }

    const activeTracks = [...this.tracks.values()]
      .filter(track => track.breachStartMs !== null)
      .sort((a, b) => a.id - b.id);
    const pendingOrNear = currentTracks.some(track => track.nearZone)
      || [...this.tracks.values()].some(track => (
        track.insideSinceMs !== null && track.breachStartMs === null
      ));
    const nextState: ZoneMonitorState = activeTracks.length > 0
      ? 'red'
      : pendingOrNear
        ? 'yellow'
        : 'green';
    const previousState = this.state;
    const enteredRed = previousState !== 'red' && nextState === 'red';
    const stateChangedAtMs = previousState === nextState
      ? null
      : previousState === 'red' && nextState !== 'red' && endedAtMs.length > 0
        ? Math.max(...endedAtMs)
        : nowMs;
    this.state = nextState;

    return {
      state: nextState,
      enteredRed,
      stateChangedAtMs,
      tracks: currentTracks.map(track => ({
        ...track.detection,
        trackId: track.id,
        insideZone: track.insideZone,
        pendingEntry: track.insideZone && track.breachStartMs === null,
        breachActive: track.breachStartMs !== null,
        footPoint: track.footPoint,
      })),
      activeBreachTrackIds: activeTracks.map(track => track.id),
      personEvents: [
        ...this.completedEvents,
        ...activeTracks.map(track => ({
          trackId: track.id,
          startMs: track.breachStartMs as number,
          endMs: nowMs,
          maxConfidence: track.maxConfidence,
        })),
      ],
    };
  }

  private matchDetections(
    detections: Detection[],
    imageWidth: number,
    imageHeight: number,
    nowMs: number,
  ) {
    const availableTracks = [...this.tracks.values()]
      .filter(track => nowMs - track.lastSeenMs <= this.config.trackerMaxGapMs);
    const candidates: Array<{ detectionIndex: number; track: Track; score: number }> = [];
    const diagonal = Math.hypot(imageWidth, imageHeight);

    detections.forEach((detection, detectionIndex) => {
      const foot = detectionFootPoint(detection, imageWidth, imageHeight, false);
      for (const track of availableTracks) {
        const overlap = intersectionOverUnion(detection, track.detection);
        const previousFoot = detectionFootPoint(track.detection, imageWidth, imageHeight, false);
        const distance = Math.hypot(foot.x - previousFoot.x, foot.y - previousFoot.y);
        const withinDistance = diagonal > 0 && distance / diagonal <= this.config.matchDistanceRatio;
        if (overlap >= this.config.matchIouThreshold || withinDistance) {
          candidates.push({
            detectionIndex,
            track,
            score: overlap + (withinDistance ? 1 - distance / diagonal : 0),
          });
        }
      }
    });

    candidates.sort((a, b) => b.score - a.score);
    const assignedDetections = new Set<number>();
    const assignedTracks = new Set<number>();
    const matches: Array<{ detection: Detection; track: Track }> = [];

    for (const candidate of candidates) {
      if (
        assignedDetections.has(candidate.detectionIndex)
        || assignedTracks.has(candidate.track.id)
      ) {
        continue;
      }
      assignedDetections.add(candidate.detectionIndex);
      assignedTracks.add(candidate.track.id);
      matches.push({ detection: detections[candidate.detectionIndex], track: candidate.track });
    }

    detections.forEach((detection, detectionIndex) => {
      if (assignedDetections.has(detectionIndex)) return;
      const track: Track = {
        id: this.nextTrackId++,
        detection,
        firstSeenMs: nowMs,
        lastSeenMs: nowMs,
        insideSinceMs: null,
        lastInsideMs: null,
        breachStartMs: null,
        maxConfidence: detection.confidence,
        insideZone: false,
        nearZone: false,
        footPoint: detectionFootPoint(detection, imageWidth, imageHeight),
      };
      this.tracks.set(track.id, track);
      matches.push({ detection, track });
    });

    return matches;
  }

  private closeEvent(track: Track, endMs: number) {
    if (track.breachStartMs === null) return null;
    const normalizedEndMs = Math.max(track.breachStartMs, endMs);
    this.completedEvents.push({
      trackId: track.id,
      startMs: track.breachStartMs,
      endMs: normalizedEndMs,
      maxConfidence: track.maxConfidence,
    });
    track.breachStartMs = null;
    track.insideSinceMs = null;
    track.lastInsideMs = null;
    return normalizedEndMs;
  }
}

export function detectionFootPoint(
  detection: Detection,
  imageWidth: number,
  imageHeight: number,
  normalized = true,
): Point {
  const x = (detection.x1 + detection.x2) / 2;
  const y = detection.y2;
  return normalized
    ? { x: x / imageWidth, y: y / imageHeight }
    : { x, y };
}

function intersectionOverUnion(a: Detection, b: Detection) {
  const x1 = Math.max(a.x1, b.x1);
  const y1 = Math.max(a.y1, b.y1);
  const x2 = Math.min(a.x2, b.x2);
  const y2 = Math.min(a.y2, b.y2);
  const intersection = Math.max(0, x2 - x1) * Math.max(0, y2 - y1);
  const areaA = Math.max(0, a.x2 - a.x1) * Math.max(0, a.y2 - a.y1);
  const areaB = Math.max(0, b.x2 - b.x1) * Math.max(0, b.y2 - b.y1);
  const union = areaA + areaB - intersection;
  return union > 0 ? intersection / union : 0;
}
