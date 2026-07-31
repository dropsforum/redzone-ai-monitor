export type BreachSegmentState = 'clear' | 'breach';
export type BreachAggregateMode = 'minute' | 'hour';

export interface BreachSegment {
  startMs: number;
  endMs: number;
  state: BreachSegmentState;
}

export interface BreachBucket {
  startMs: number;
  endMs: number;
  breachMs: number;
  clearMs: number;
  totalMs: number;
  breachPercent: number;
}

export interface BreachSnapshot {
  segments: BreachSegment[];
  buckets: BreachBucket[];
  totalBreachMs: number;
  totalClearMs: number;
  totalMs: number;
  currentState: BreachSegmentState;
  activeBreachMs: number;
  breachCount: number;
  clearCount: number;
  periodStartMs: number | null;
  periodEndMs: number | null;
}

const BUCKET_MS: Record<BreachAggregateMode, number> = {
  minute: 60_000,
  hour: 3_600_000,
};

function floorToBucket(timestampMs: number, bucketMs: number) {
  return Math.floor(timestampMs / bucketMs) * bucketMs;
}

function pushDuration(bucket: BreachBucket, state: BreachSegmentState, durationMs: number) {
  if (state === 'breach') bucket.breachMs += durationMs;
  else bucket.clearMs += durationMs;
  bucket.totalMs = bucket.breachMs + bucket.clearMs;
  bucket.breachPercent = bucket.totalMs > 0 ? (bucket.breachMs / bucket.totalMs) * 100 : 0;
}

export class BreachRecorder {
  private completedSegments: BreachSegment[] = [];
  private activeSegment: BreachSegment | null = null;
  private running = false;

  start(nowMs = Date.now()) {
    if (this.running) return;
    this.running = true;
    this.activeSegment = { startMs: nowMs, endMs: nowMs, state: 'clear' };
  }

  stop(nowMs = Date.now()) {
    if (!this.running) return;
    this.closeActive(nowMs);
    this.running = false;
    this.activeSegment = null;
  }

  reset() {
    this.completedSegments = [];
    this.activeSegment = null;
    this.running = false;
  }

  update(isBreach: boolean, nowMs = Date.now()) {
    if (!this.running) return;
    const nextState: BreachSegmentState = isBreach ? 'breach' : 'clear';

    if (!this.activeSegment) {
      this.activeSegment = { startMs: nowMs, endMs: nowMs, state: nextState };
      return;
    }

    if (this.activeSegment.state === nextState) {
      this.activeSegment.endMs = Math.max(this.activeSegment.endMs, nowMs);
      return;
    }

    this.closeActive(nowMs);
    this.activeSegment = { startMs: nowMs, endMs: nowMs, state: nextState };
  }

  snapshot(mode: BreachAggregateMode, nowMs = Date.now()): BreachSnapshot {
    return summarizeBreachSegments(this.getSegments(nowMs), mode);
  }

  private closeActive(nowMs: number) {
    if (!this.activeSegment) return;
    this.completedSegments.push({
      ...this.activeSegment,
      endMs: Math.max(this.activeSegment.startMs, nowMs),
    });
  }

  private getSegments(nowMs: number) {
    const segments = [...this.completedSegments];
    if (this.running && this.activeSegment) {
      segments.push({
        ...this.activeSegment,
        endMs: Math.max(this.activeSegment.endMs, nowMs),
      });
    }
    return segments.filter(segment => segment.endMs > segment.startMs);
  }
}

export function summarizeBreachSegments(
  inputSegments: BreachSegment[],
  mode: BreachAggregateMode,
): BreachSnapshot {
    const segments = inputSegments.map(segment => ({ ...segment }));
    const buckets = aggregateSegments(segments, mode);
    const totalBreachMs = segments
      .filter(segment => segment.state === 'breach')
      .reduce((sum, segment) => sum + Math.max(0, segment.endMs - segment.startMs), 0);
    const totalClearMs = segments
      .filter(segment => segment.state === 'clear')
      .reduce((sum, segment) => sum + Math.max(0, segment.endMs - segment.startMs), 0);
    const active = segments.at(-1);

    return {
      segments,
      buckets,
      totalBreachMs,
      totalClearMs,
      totalMs: totalBreachMs + totalClearMs,
      currentState: active?.state ?? 'clear',
      activeBreachMs: active?.state === 'breach' ? Math.max(0, active.endMs - active.startMs) : 0,
      breachCount: segments.filter(segment => segment.state === 'breach').length,
      clearCount: segments.filter(segment => segment.state === 'clear').length,
      periodStartMs: segments[0]?.startMs ?? null,
      periodEndMs: segments.at(-1)?.endMs ?? null,
    };
}

export function aggregateSegments(segments: BreachSegment[], mode: BreachAggregateMode): BreachBucket[] {
  const bucketMs = BUCKET_MS[mode];
  const buckets = new Map<number, BreachBucket>();

  for (const segment of segments) {
    let cursor = segment.startMs;
    while (cursor < segment.endMs) {
      const bucketStart = floorToBucket(cursor, bucketMs);
      const bucketEnd = bucketStart + bucketMs;
      const sliceEnd = Math.min(segment.endMs, bucketEnd);
      const durationMs = Math.max(0, sliceEnd - cursor);

      const bucket = buckets.get(bucketStart) ?? {
        startMs: bucketStart,
        endMs: bucketEnd,
        breachMs: 0,
        clearMs: 0,
        totalMs: 0,
        breachPercent: 0,
      };

      pushDuration(bucket, segment.state, durationMs);
      buckets.set(bucketStart, bucket);
      cursor = sliceEnd;
    }
  }

  return Array.from(buckets.values()).sort((a, b) => a.startMs - b.startMs);
}

export function formatDuration(durationMs: number) {
  const totalSeconds = Math.max(0, Math.round(durationMs / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}

export function formatBucketLabel(timestampMs: number, mode: BreachAggregateMode) {
  const date = new Date(timestampMs);
  if (mode === 'hour') {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function csvEscape(value: string | number) {
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function formatLocalDateTime(timestampMs: number) {
  return new Date(timestampMs).toLocaleString([], {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export function breachSegmentsToCsv(segments: BreachSegment[]) {
  const rows = [
    ['record_type', 'start_datetime', 'end_datetime', 'start_iso', 'end_iso', 'duration_seconds'],
    ...segments.map(segment => [
      segment.state === 'breach' ? 'BREACH' : 'NO_BREACH',
      formatLocalDateTime(segment.startMs),
      formatLocalDateTime(segment.endMs),
      new Date(segment.startMs).toISOString(),
      new Date(segment.endMs).toISOString(),
      ((segment.endMs - segment.startMs) / 1000).toFixed(2),
    ]),
  ];

  return rows.map(row => row.map(csvEscape).join(',')).join('\n');
}

export function breachMetricsToCsv(snapshot: BreachSnapshot, mode: BreachAggregateMode) {
  const rows = [
    ['metric', 'value'],
    ['period_start', snapshot.periodStartMs ? formatLocalDateTime(snapshot.periodStartMs) : ''],
    ['period_end', snapshot.periodEndMs ? formatLocalDateTime(snapshot.periodEndMs) : ''],
    ['aggregate_mode', mode],
    ['observed_seconds', (snapshot.totalMs / 1000).toFixed(2)],
    ['breach_seconds', (snapshot.totalBreachMs / 1000).toFixed(2)],
    ['no_breach_seconds', (snapshot.totalClearMs / 1000).toFixed(2)],
    ['breach_percent', snapshot.totalMs > 0 ? ((snapshot.totalBreachMs / snapshot.totalMs) * 100).toFixed(2) : '0.00'],
    ['breach_record_count', snapshot.breachCount],
    ['no_breach_record_count', snapshot.clearCount],
    [],
    ['bucket_start', 'bucket_end', 'breach_seconds', 'no_breach_seconds', 'total_seconds', 'breach_percent'],
    ...snapshot.buckets.map(bucket => [
      formatLocalDateTime(bucket.startMs),
      formatLocalDateTime(bucket.endMs),
      (bucket.breachMs / 1000).toFixed(2),
      (bucket.clearMs / 1000).toFixed(2),
      (bucket.totalMs / 1000).toFixed(2),
      bucket.breachPercent.toFixed(2),
    ]),
  ];

  return rows.map(row => row.map(csvEscape).join(',')).join('\n');
}

export function breachBucketsToCsv(buckets: BreachBucket[]) {
  const rows = [
    ['bucket_start', 'bucket_end', 'breach_seconds', 'clear_seconds', 'total_seconds', 'breach_percent'],
    ...buckets.map(bucket => [
      new Date(bucket.startMs).toISOString(),
      new Date(bucket.endMs).toISOString(),
      (bucket.breachMs / 1000).toFixed(2),
      (bucket.clearMs / 1000).toFixed(2),
      (bucket.totalMs / 1000).toFixed(2),
      bucket.breachPercent.toFixed(2),
    ]),
  ];

  return rows.map(row => row.join(',')).join('\n');
}
