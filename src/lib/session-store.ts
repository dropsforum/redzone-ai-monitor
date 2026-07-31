import type { Point } from '../components/ZoneEditor';
import type { BreachSegment } from './breach-recorder';
import type { PersonBreachEvent } from './zone-monitor';

export type MonitoringSessionStatus = 'active' | 'completed' | 'interrupted';

export interface MonitoringSession {
  id: string;
  startedAtMs: number;
  endedAtMs: number | null;
  lastHeartbeatMs: number;
  status: MonitoringSessionStatus;
  sourceMode: 'camera' | 'file';
  sourceLabel: string;
  modelName: string;
  modelVersion: string;
  backend: string;
  zone: Point[];
  entryConfirmMs: number;
  exitGraceMs: number;
  trackerMaxGapMs: number;
  warningBuffer: number;
}

export interface InferenceHealth {
  observedFps: number;
  inferenceSamples: number;
  averagePreprocessMs: number;
  averageInferenceMs: number;
  averagePostprocessMs: number;
  maxInferenceMs: number;
  droppedInferenceRequests: number;
  detectorErrors: number;
}

export interface MonitoringSessionArchive {
  session: MonitoringSession;
  segments: BreachSegment[];
  personEvents: PersonBreachEvent[];
  health: InferenceHealth;
}

export type NewMonitoringSession = Pick<
  MonitoringSession,
  'sourceMode' | 'sourceLabel' | 'zone' | 'modelName' | 'modelVersion' | 'backend'
> & Partial<Pick<
  MonitoringSession,
  'id' | 'startedAtMs' | 'entryConfirmMs' | 'exitGraceMs' | 'trackerMaxGapMs' | 'warningBuffer'
>>;

const DB_VERSION = 1;
const STORE_NAME = 'sessions';

export function createMonitoringSession(input: NewMonitoringSession): MonitoringSession {
  const startedAtMs = input.startedAtMs ?? Date.now();
  return {
    id: input.id ?? createId(),
    startedAtMs,
    endedAtMs: null,
    lastHeartbeatMs: startedAtMs,
    status: 'active',
    sourceMode: input.sourceMode,
    sourceLabel: input.sourceLabel,
    modelName: input.modelName,
    modelVersion: input.modelVersion,
    backend: input.backend,
    zone: input.zone.map(point => ({ ...point })),
    entryConfirmMs: input.entryConfirmMs ?? 300,
    exitGraceMs: input.exitGraceMs ?? 750,
    trackerMaxGapMs: input.trackerMaxGapMs ?? 750,
    warningBuffer: input.warningBuffer ?? 0.1,
  };
}

export class BrowserSessionStore {
  private openPromise: Promise<IDBDatabase> | null = null;

  constructor(
    private readonly dbName = 'drops-red-zone-monitor',
    private readonly factory: IDBFactory = globalThis.indexedDB,
  ) {}

  async save(archive: MonitoringSessionArchive) {
    const db = await this.open();
    const transaction = db.transaction(STORE_NAME, 'readwrite');
    transaction.objectStore(STORE_NAME).put(structuredClone(archive), archive.session.id);
    await transactionDone(transaction);
  }

  async get(id: string): Promise<MonitoringSessionArchive | null> {
    const db = await this.open();
    const transaction = db.transaction(STORE_NAME, 'readonly');
    const result = await requestResult<MonitoringSessionArchive | undefined>(
      transaction.objectStore(STORE_NAME).get(id),
    );
    await transactionDone(transaction);
    return result ?? null;
  }

  async list(): Promise<MonitoringSessionArchive[]> {
    const db = await this.open();
    const transaction = db.transaction(STORE_NAME, 'readonly');
    const results = await requestResult<MonitoringSessionArchive[]>(
      transaction.objectStore(STORE_NAME).getAll(),
    );
    await transactionDone(transaction);
    return results.sort((a, b) => b.session.startedAtMs - a.session.startedAtMs);
  }

  async recoverInterruptedSessions(nowMs = Date.now()) {
    const archives = await this.list();
    const recovered: MonitoringSessionArchive[] = [];

    for (const archive of archives) {
      if (archive.session.status !== 'active') continue;
      const endedAtMs = Math.min(archive.session.lastHeartbeatMs, nowMs);
      archive.session.status = 'interrupted';
      archive.session.endedAtMs = endedAtMs;
      const activeSegment = archive.segments.at(-1);
      if (activeSegment) activeSegment.endMs = Math.max(activeSegment.startMs, endedAtMs);
      for (const event of archive.personEvents) {
        event.endMs = Math.min(Math.max(event.startMs, event.endMs), endedAtMs);
      }
      await this.save(archive);
      recovered.push(archive);
    }
    return recovered;
  }

  private open() {
    if (!this.factory) {
      return Promise.reject(new Error('IndexedDB is unavailable in this browser'));
    }
    this.openPromise ??= new Promise<IDBDatabase>((resolve, reject) => {
      const request = this.factory.open(this.dbName, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) db.createObjectStore(STORE_NAME);
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error ?? new Error('Unable to open monitoring database'));
    });
    return this.openPromise;
  }
}

function requestResult<T>(request: IDBRequest<T>) {
  return new Promise<T>((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error('IndexedDB request failed'));
  });
}

function transactionDone(transaction: IDBTransaction) {
  return new Promise<void>((resolve, reject) => {
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error ?? new Error('IndexedDB transaction failed'));
    transaction.onabort = () => reject(transaction.error ?? new Error('IndexedDB transaction aborted'));
  });
}

function createId() {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
