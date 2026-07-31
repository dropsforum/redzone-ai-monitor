import { describe, expect, it } from 'vitest';

import fixture from '../../tests/fixtures/zone_sequences.json';
import { BreachRecorder } from './breach-recorder';
import type { Detection } from './yolo-detector';
import { ZoneMonitor } from './zone-monitor';

const zone = [
  { x: 0.4, y: 0.4 },
  { x: 0.6, y: 0.4 },
  { x: 0.6, y: 0.8 },
  { x: 0.4, y: 0.8 },
];

function person(x1: number, y1: number, x2: number, y2: number, confidence = 0.8): Detection {
  return { x1, y1, x2, y2, confidence, classId: 0 };
}

describe('zone monitor', () => {
  it('confirms a foot-point breach after 300ms and applies exit grace', () => {
    const monitor = new ZoneMonitor();
    const inZone = person(450, 300, 550, 700);

    expect(monitor.update([inZone], zone, 1000, 1000, 0).state).toBe('yellow');
    const confirmed = monitor.update([inZone], zone, 1000, 1000, 300);
    expect(confirmed.state).toBe('red');
    expect(confirmed.enteredRed).toBe(true);

    expect(monitor.update([], zone, 1000, 1000, 900).state).toBe('red');
    const cleared = monitor.update([], zone, 1000, 1000, 1100);
    expect(cleared.state).toBe('green');
    expect(cleared.personEvents).toEqual([
      expect.objectContaining({
        trackId: 1,
        startMs: 0,
        endMs: 1050,
      }),
    ]);
  });

  it('keeps separate events for two people', () => {
    const monitor = new ZoneMonitor();
    const first = person(420, 300, 480, 700, 0.75);
    const second = person(520, 300, 580, 700, 0.9);

    monitor.update([first, second], zone, 1000, 1000, 0);
    const confirmed = monitor.update([first, second], zone, 1000, 1000, 300);
    expect(confirmed.activeBreachTrackIds).toEqual([1, 2]);

    const stopped = monitor.stop(1000);
    expect(stopped.personEvents.map(event => event.trackId)).toEqual([1, 2]);
  });

  it('retains a track through a brief detection gap', () => {
    const monitor = new ZoneMonitor();
    const inZone = person(450, 300, 550, 700);

    monitor.update([inZone], zone, 1000, 1000, 0);
    monitor.update([], zone, 1000, 1000, 100);
    const resumed = monitor.update([person(455, 305, 555, 705)], zone, 1000, 1000, 300);

    expect(resumed.tracks[0].trackId).toBe(1);
    expect(resumed.state).toBe('red');
  });

  it('uses the bottom-centre point rather than box corners', () => {
    const monitor = new ZoneMonitor();
    const overlapsButStandsOutside = person(450, 300, 550, 850);

    const snapshot = monitor.update([overlapsButStandsOutside], zone, 1000, 1000, 0);

    expect(snapshot.state).not.toBe('red');
    expect(snapshot.tracks[0].insideZone).toBe(false);
  });

  it('matches the shared cross-platform state and reporting fixture', () => {
    for (const sequence of fixture.sequences) {
      const monitor = new ZoneMonitor({
        entryConfirmMs: fixture.config.entryConfirmMs,
        exitGraceMs: fixture.config.exitGraceMs,
        trackerMaxGapMs: fixture.config.trackerMaxGapMs,
        warningBuffer: fixture.config.warningBuffer,
      });
      const recorder = new BreachRecorder();
      recorder.start(sequence.steps[0].atMs);
      let snapshot = monitor.update(
        [],
        fixture.zone,
        fixture.frame.width,
        fixture.frame.height,
        sequence.steps[0].atMs,
      );

      for (const step of sequence.steps) {
        const detections = step.detections.map(item => person(
          item.box[0],
          item.box[1],
          item.box[2],
          item.box[3],
          item.confidence,
        ));
        snapshot = monitor.update(
          detections,
          fixture.zone,
          fixture.frame.width,
          fixture.frame.height,
          step.atMs,
        );
        expect(snapshot.state, `${sequence.name} at ${step.atMs}ms`).toBe(step.expectedState);
        recorder.update(
          snapshot.state === 'red',
          snapshot.stateChangedAtMs ?? step.atMs,
        );
      }

      const finalTime = sequence.steps.at(-1)?.atMs ?? 0;
      recorder.stop(finalTime);
      expect(snapshot.personEvents).toEqual(sequence.expectedPersonEvents);
      expect(recorder.snapshot('minute', finalTime).segments).toEqual(
        sequence.expectedSegments,
      );
    }
  });
});
