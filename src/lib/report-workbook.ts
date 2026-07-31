import { strToU8, zipSync } from 'fflate';

import {
  aggregateSegments,
  type BreachAggregateMode,
} from './breach-recorder';
import type { MonitoringSessionArchive } from './session-store';

type CellValue = string | number | null;
type Sheet = { name: string; rows: CellValue[][] };

export async function buildSessionWorkbook(
  archive: MonitoringSessionArchive,
  mode: BreachAggregateMode,
): Promise<Uint8Array> {
  const sheets = buildSheets(archive, mode);
  const files: Record<string, Uint8Array> = {
    '[Content_Types].xml': xml(_contentTypes(sheets.length)),
    '_rels/.rels': xml(ROOT_RELS),
    'xl/workbook.xml': xml(_workbook(sheets)),
    'xl/_rels/workbook.xml.rels': xml(_workbookRels(sheets.length)),
    'xl/styles.xml': xml(STYLES),
  };
  sheets.forEach((sheet, index) => {
    files[`xl/worksheets/sheet${index + 1}.xml`] = xml(_worksheet(sheet.rows));
  });
  return zipSync(files, { level: 6 });
}

function buildSheets(
  archive: MonitoringSessionArchive,
  mode: BreachAggregateMode,
): Sheet[] {
  const { session, segments, personEvents, health } = archive;
  const buckets = aggregateSegments(segments, mode);
  const breachMs = segments
    .filter(segment => segment.state === 'breach')
    .reduce((sum, segment) => sum + segment.endMs - segment.startMs, 0);
  const clearMs = segments
    .filter(segment => segment.state === 'clear')
    .reduce((sum, segment) => sum + segment.endMs - segment.startMs, 0);
  const totalMs = breachMs + clearMs;

  return [
    {
      name: 'Records',
      rows: [
        ['record_type', 'start_datetime', 'end_datetime', 'start_iso', 'end_iso', 'duration_seconds'],
        ...segments.map(segment => [
          segment.state === 'breach' ? 'BREACH' : 'NO_BREACH',
          localDateTime(segment.startMs),
          localDateTime(segment.endMs),
          new Date(segment.startMs).toISOString(),
          new Date(segment.endMs).toISOString(),
          round((segment.endMs - segment.startMs) / 1000),
        ]),
      ],
    },
    {
      name: 'Person Breaches',
      rows: [
        ['track_id', 'start_datetime', 'end_datetime', 'start_iso', 'end_iso', 'duration_seconds', 'max_confidence'],
        ...personEvents.map(event => [
          event.trackId,
          localDateTime(event.startMs),
          localDateTime(event.endMs),
          new Date(event.startMs).toISOString(),
          new Date(event.endMs).toISOString(),
          round((event.endMs - event.startMs) / 1000),
          round(event.maxConfidence, 4),
        ]),
      ],
    },
    {
      name: 'Aggregated Results',
      rows: [
        ['bucket_start', 'bucket_end', 'breach_seconds', 'no_breach_seconds', 'total_seconds', 'breach_percent'],
        ...buckets.map(bucket => [
          localDateTime(bucket.startMs),
          localDateTime(bucket.endMs),
          round(bucket.breachMs / 1000),
          round(bucket.clearMs / 1000),
          round(bucket.totalMs / 1000),
          round(bucket.breachPercent),
        ]),
      ],
    },
    {
      name: 'Overall Metrics',
      rows: [
        ['metric', 'value'],
        ['period_start', localDateTime(session.startedAtMs)],
        ['period_end', session.endedAtMs ? localDateTime(session.endedAtMs) : ''],
        ['aggregate_mode', mode],
        ['observed_seconds', round(totalMs / 1000)],
        ['breach_seconds', round(breachMs / 1000)],
        ['no_breach_seconds', round(clearMs / 1000)],
        ['breach_percent', totalMs > 0 ? round((breachMs / totalMs) * 100) : 0],
        ['breach_record_count', segments.filter(segment => segment.state === 'breach').length],
        ['no_breach_record_count', segments.filter(segment => segment.state === 'clear').length],
        ['person_breach_count', personEvents.length],
        ['observed_fps', health.observedFps],
        ['average_preprocess_ms', health.averagePreprocessMs],
        ['average_inference_ms', health.averageInferenceMs],
        ['average_postprocess_ms', health.averagePostprocessMs],
        ['maximum_inference_ms', health.maxInferenceMs],
        ['dropped_inference_requests', health.droppedInferenceRequests],
        ['detector_errors', health.detectorErrors],
      ],
    },
    {
      name: 'Session Metadata',
      rows: [
        ['field', 'value'],
        ['session_id', session.id],
        ['status', session.status],
        ['source_mode', session.sourceMode],
        ['source_label', session.sourceLabel],
        ['model_name', session.modelName],
        ['model_version', session.modelVersion],
        ['backend', session.backend],
        ['entry_confirm_ms', session.entryConfirmMs],
        ['exit_grace_ms', session.exitGraceMs],
        ['tracker_max_gap_ms', session.trackerMaxGapMs],
        ['warning_buffer', session.warningBuffer],
        ['zone_points', JSON.stringify(session.zone)],
      ],
    },
  ];
}

function _contentTypes(sheetCount: number) {
  const worksheets = Array.from({ length: sheetCount }, (_, index) => (
    `<Override PartName="/xl/worksheets/sheet${index + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>`
  )).join('');
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
    + `<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">`
    + `<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>`
    + `<Default Extension="xml" ContentType="application/xml"/>`
    + `<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>`
    + `<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>`
    + `${worksheets}</Types>`;
}

function _workbook(sheets: Sheet[]) {
  const sheetXml = sheets.map((sheet, index) => (
    `<sheet name="${escapeXml(sheet.name)}" sheetId="${index + 1}" r:id="rId${index + 1}"/>`
  )).join('');
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
    + `<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" `
    + `xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">`
    + `<sheets>${sheetXml}</sheets></workbook>`;
}

function _workbookRels(sheetCount: number) {
  const sheetRels = Array.from({ length: sheetCount }, (_, index) => (
    `<Relationship Id="rId${index + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet${index + 1}.xml"/>`
  )).join('');
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
    + `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">`
    + `${sheetRels}<Relationship Id="rId${sheetCount + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>`
    + `</Relationships>`;
}

function _worksheet(rows: CellValue[][]) {
  const rowXml = rows.map((row, rowIndex) => {
    const cells = row.map((value, columnIndex) => {
      const ref = `${columnName(columnIndex)}${rowIndex + 1}`;
      const style = rowIndex === 0 ? ' s="1"' : '';
      if (typeof value === 'number') {
        return `<c r="${ref}"${style}><v>${Number.isFinite(value) ? value : 0}</v></c>`;
      }
      return `<c r="${ref}" t="inlineStr"${style}><is><t>${escapeXml(value ?? '')}</t></is></c>`;
    }).join('');
    return `<row r="${rowIndex + 1}">${cells}</row>`;
  }).join('');
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
    + `<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">`
    + `<sheetData>${rowXml}</sheetData></worksheet>`;
}

function columnName(index: number) {
  let name = '';
  let cursor = index + 1;
  while (cursor > 0) {
    cursor -= 1;
    name = String.fromCharCode(65 + (cursor % 26)) + name;
    cursor = Math.floor(cursor / 26);
  }
  return name;
}

function localDateTime(timestampMs: number) {
  return new Date(timestampMs).toLocaleString([], {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function round(value: number, digits = 2) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function escapeXml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}

function xml(value: string) {
  return strToU8(value);
}

const ROOT_RELS = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
  + `<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">`
  + `<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>`
  + `</Relationships>`;

const STYLES = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>`
  + `<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">`
  + `<fonts count="2"><font><sz val="11"/><name val="Arial"/></font><font><b/><sz val="11"/><name val="Arial"/></font></fonts>`
  + `<fills count="1"><fill><patternFill patternType="none"/></fill></fills>`
  + `<borders count="1"><border/></borders>`
  + `<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>`
  + `<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>`
  + `<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1"/></cellXfs>`
  + `</styleSheet>`;
