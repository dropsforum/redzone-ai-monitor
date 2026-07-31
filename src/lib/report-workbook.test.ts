import { strFromU8, unzipSync } from 'fflate';
import { describe, expect, it } from 'vitest';

import { buildSessionWorkbook } from './report-workbook';
import { createMonitoringSession, type MonitoringSessionArchive } from './session-store';

describe('browser Excel session report', () => {
  it('contains all five required report sheets', async () => {
    const archive: MonitoringSessionArchive = {
      session: {
        ...createMonitoringSession({
          id: 'session-1',
          startedAtMs: 1000,
          sourceMode: 'file',
          sourceLabel: 'clip.mp4',
          zone: [],
          modelName: 'yolo26n',
          modelVersion: '8.4.112',
          backend: 'onnx-wasm',
        }),
        endedAtMs: 4000,
        lastHeartbeatMs: 4000,
        status: 'completed',
      },
      segments: [
        { startMs: 1000, endMs: 2000, state: 'clear' },
        { startMs: 2000, endMs: 4000, state: 'breach' },
      ],
      personEvents: [{ trackId: 7, startMs: 2000, endMs: 4000, maxConfidence: 0.91 }],
      health: {
        observedFps: 10,
        inferenceSamples: 5,
        averagePreprocessMs: 2,
        averageInferenceMs: 20,
        averagePostprocessMs: 1,
        maxInferenceMs: 25,
        droppedInferenceRequests: 1,
        detectorErrors: 0,
      },
    };

    const workbook = unzipSync(await buildSessionWorkbook(archive, 'minute'));
    const workbookXml = strFromU8(workbook['xl/workbook.xml']);

    expect(workbookXml).toContain('name="Records"');
    expect(workbookXml).toContain('name="Person Breaches"');
    expect(workbookXml).toContain('name="Aggregated Results"');
    expect(workbookXml).toContain('name="Overall Metrics"');
    expect(workbookXml).toContain('name="Session Metadata"');
    expect(strFromU8(workbook['xl/worksheets/sheet2.xml'])).toContain('0.91');
  });
});
