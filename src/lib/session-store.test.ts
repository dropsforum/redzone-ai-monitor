import 'fake-indexeddb/auto';

import { describe, expect, it } from 'vitest';

import {
  BrowserSessionStore,
  createMonitoringSession,
  type MonitoringSessionArchive,
} from './session-store';

describe('browser monitoring session persistence', () => {
  it('closes an interrupted session at its last heartbeat', async () => {
    const store = new BrowserSessionStore(`red-zone-test-${crypto.randomUUID()}`);
    const archive: MonitoringSessionArchive = {
      session: createMonitoringSession({
        id: 'session-1',
        startedAtMs: 100,
        sourceMode: 'camera',
        sourceLabel: 'Camera 1',
        zone: [{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 1, y: 1 }],
        modelName: 'yolo26n',
        modelVersion: '8.4.112',
        backend: 'onnx-wasm',
      }),
      segments: [{ startMs: 100, endMs: 500, state: 'clear' }],
      personEvents: [],
      health: {
        observedFps: 10,
        inferenceSamples: 4,
        averagePreprocessMs: 2,
        averageInferenceMs: 20,
        averagePostprocessMs: 1,
        maxInferenceMs: 24,
        droppedInferenceRequests: 0,
        detectorErrors: 0,
      },
    };
    archive.session.lastHeartbeatMs = 500;

    await store.save(archive);
    const recovered = await store.recoverInterruptedSessions(1000);
    const persisted = await store.get('session-1');

    expect(recovered).toHaveLength(1);
    expect(persisted?.session.status).toBe('interrupted');
    expect(persisted?.session.endedAtMs).toBe(500);
  });

  it('lists newest sessions first', async () => {
    const store = new BrowserSessionStore(`red-zone-test-${crypto.randomUUID()}`);
    for (const [id, startedAtMs] of [['old', 100], ['new', 200]] as const) {
      await store.save({
        session: createMonitoringSession({
          id,
          startedAtMs,
          sourceMode: 'file',
          sourceLabel: 'clip.mp4',
          zone: [],
          modelName: 'yolo26n',
          modelVersion: '8.4.112',
          backend: 'onnx-wasm',
        }),
        segments: [],
        personEvents: [],
        health: {
          observedFps: 0,
          inferenceSamples: 0,
          averagePreprocessMs: 0,
          averageInferenceMs: 0,
          averagePostprocessMs: 0,
          maxInferenceMs: 0,
          droppedInferenceRequests: 0,
          detectorErrors: 0,
        },
      });
    }

    expect((await store.list()).map(archive => archive.session.id)).toEqual(['new', 'old']);
  });
});
