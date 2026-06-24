"""In-session red-zone breach duration recorder."""

from __future__ import annotations

import csv
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal
from xml.sax.saxutils import escape

BreachState = Literal["clear", "breach"]
AggregateMode = Literal["minute", "hour"]


@dataclass
class BreachSegment:
    start: float
    end: float
    state: BreachState


@dataclass
class BreachBucket:
    start: float
    end: float
    breach_seconds: float = 0.0
    clear_seconds: float = 0.0

    @property
    def total_seconds(self) -> float:
        return self.breach_seconds + self.clear_seconds

    @property
    def breach_percent(self) -> float:
        if self.total_seconds <= 0:
            return 0.0
        return (self.breach_seconds / self.total_seconds) * 100.0


class BreachRecorder:
    def __init__(self):
        self.completed: list[BreachSegment] = []
        self.active: BreachSegment | None = None
        self.running = False

    def start(self, now: float | None = None):
        if self.running:
            return
        now = time.time() if now is None else now
        self.running = True
        self.active = BreachSegment(now, now, "clear")

    def stop(self, now: float | None = None):
        if not self.running:
            return
        now = time.time() if now is None else now
        self._close_active(now)
        self.active = None
        self.running = False

    def reset(self):
        self.completed.clear()
        self.active = None
        self.running = False

    def update(self, is_breach: bool, now: float | None = None):
        if not self.running:
            return
        now = time.time() if now is None else now
        next_state: BreachState = "breach" if is_breach else "clear"
        if self.active is None:
            self.active = BreachSegment(now, now, next_state)
            return
        if self.active.state == next_state:
            self.active.end = max(self.active.end, now)
            return
        self._close_active(now)
        self.active = BreachSegment(now, now, next_state)

    def segments(self, now: float | None = None) -> list[BreachSegment]:
        now = time.time() if now is None else now
        segments = list(self.completed)
        if self.running and self.active is not None:
            segments.append(BreachSegment(self.active.start, max(self.active.end, now), self.active.state))
        return [segment for segment in segments if segment.end > segment.start]

    def buckets(self, mode: AggregateMode, now: float | None = None) -> list[BreachBucket]:
        bucket_seconds = 60.0 if mode == "minute" else 3600.0
        buckets: dict[float, BreachBucket] = {}
        for segment in self.segments(now):
            cursor = segment.start
            while cursor < segment.end:
                bucket_start = cursor - (cursor % bucket_seconds)
                bucket_end = bucket_start + bucket_seconds
                slice_end = min(segment.end, bucket_end)
                duration = max(0.0, slice_end - cursor)
                bucket = buckets.setdefault(bucket_start, BreachBucket(bucket_start, bucket_end))
                if segment.state == "breach":
                    bucket.breach_seconds += duration
                else:
                    bucket.clear_seconds += duration
                cursor = slice_end
        return [buckets[key] for key in sorted(buckets)]

    def summary(self, mode: AggregateMode = "minute") -> dict[str, float | int | str]:
        segments = self.segments()
        breach_seconds = sum(segment.end - segment.start for segment in segments if segment.state == "breach")
        clear_seconds = sum(segment.end - segment.start for segment in segments if segment.state == "clear")
        total_seconds = breach_seconds + clear_seconds
        current = segments[-1].state if segments else "clear"
        active_breach_seconds = 0.0
        if segments and segments[-1].state == "breach":
            active_breach_seconds = segments[-1].end - segments[-1].start
        return {
            "breach_seconds": breach_seconds,
            "clear_seconds": clear_seconds,
            "total_seconds": total_seconds,
            "breach_percent": (breach_seconds / total_seconds * 100.0) if total_seconds > 0 else 0.0,
            "breach_count": sum(1 for segment in segments if segment.state == "breach"),
            "clear_count": sum(1 for segment in segments if segment.state == "clear"),
            "current_state": current,
            "active_breach_seconds": active_breach_seconds,
            "bucket_count": len(self.buckets(mode)),
            "period_start": segments[0].start if segments else 0.0,
            "period_end": segments[-1].end if segments else 0.0,
        }

    def export_records_csv(self, path: Path):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["record_type", "start_datetime", "end_datetime", "start_iso", "end_iso", "duration_seconds"])
            for segment in self.segments():
                writer.writerow([
                    "BREACH" if segment.state == "breach" else "NO_BREACH",
                    _local_datetime(segment.start),
                    _local_datetime(segment.end),
                    _iso_datetime(segment.start),
                    _iso_datetime(segment.end),
                    f"{segment.end - segment.start:.2f}",
                ])

    def export_metrics_csv(self, path: Path, mode: AggregateMode):
        summary = self.summary(mode)
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["metric", "value"])
            writer.writerows([
                ["period_start", _local_datetime(float(summary["period_start"])) if summary["period_start"] else ""],
                ["period_end", _local_datetime(float(summary["period_end"])) if summary["period_end"] else ""],
                ["aggregate_mode", mode],
                ["observed_seconds", f"{float(summary['total_seconds']):.2f}"],
                ["breach_seconds", f"{float(summary['breach_seconds']):.2f}"],
                ["no_breach_seconds", f"{float(summary['clear_seconds']):.2f}"],
                ["breach_percent", f"{float(summary['breach_percent']):.2f}"],
                ["breach_record_count", int(summary["breach_count"])],
                ["no_breach_record_count", int(summary["clear_count"])],
            ])
            writer.writerow([])
            writer.writerow(["bucket_start", "bucket_end", "breach_seconds", "no_breach_seconds", "total_seconds", "breach_percent"])
            for bucket in self.buckets(mode):
                writer.writerow([
                    _local_datetime(bucket.start),
                    _local_datetime(bucket.end),
                    f"{bucket.breach_seconds:.2f}",
                    f"{bucket.clear_seconds:.2f}",
                    f"{bucket.total_seconds:.2f}",
                    f"{bucket.breach_percent:.2f}",
                ])

    def export_excel(self, path: Path, mode: AggregateMode):
        summary = self.summary(mode)
        records_rows = [
            ["record_type", "start_datetime", "end_datetime", "start_iso", "end_iso", "duration_seconds"],
            *[
                [
                    "BREACH" if segment.state == "breach" else "NO_BREACH",
                    _local_datetime(segment.start),
                    _local_datetime(segment.end),
                    _iso_datetime(segment.start),
                    _iso_datetime(segment.end),
                    round(segment.end - segment.start, 2),
                ]
                for segment in self.segments()
            ],
        ]
        aggregated_rows = [
            ["bucket_start", "bucket_end", "breach_seconds", "no_breach_seconds", "total_seconds", "breach_percent"],
            *[
                [
                    _local_datetime(bucket.start),
                    _local_datetime(bucket.end),
                    round(bucket.breach_seconds, 2),
                    round(bucket.clear_seconds, 2),
                    round(bucket.total_seconds, 2),
                    round(bucket.breach_percent, 2),
                ]
                for bucket in self.buckets(mode)
            ],
        ]
        metrics_rows = [
            ["metric", "value"],
            ["period_start", _local_datetime(float(summary["period_start"])) if summary["period_start"] else ""],
            ["period_end", _local_datetime(float(summary["period_end"])) if summary["period_end"] else ""],
            ["aggregate_mode", mode],
            ["observed_seconds", round(float(summary["total_seconds"]), 2)],
            ["breach_seconds", round(float(summary["breach_seconds"]), 2)],
            ["no_breach_seconds", round(float(summary["clear_seconds"]), 2)],
            ["breach_percent", round(float(summary["breach_percent"]), 2)],
            ["breach_record_count", int(summary["breach_count"])],
            ["no_breach_record_count", int(summary["clear_count"])],
        ]
        _write_xlsx(
            path,
            [
                ("Records", records_rows),
                ("Aggregated Results", aggregated_rows),
                ("Overall Metrics", metrics_rows),
            ],
        )

    def _close_active(self, now: float):
        if self.active is None:
            return
        self.completed.append(BreachSegment(self.active.start, max(self.active.start, now), self.active.state))


def format_duration(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours = total // 3600
    minutes = (total % 3600) // 60
    secs = total % 60
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _local_datetime(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def _iso_datetime(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp).astimezone().isoformat(timespec="seconds")


def _write_xlsx(path: Path, sheets: list[tuple[str, list[list[object]]]]):
    if path.suffix.lower() != ".xlsx":
        path = path.with_suffix(".xlsx")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as workbook:
        workbook.writestr("[Content_Types].xml", _content_types_xml(len(sheets)))
        workbook.writestr("_rels/.rels", _root_rels_xml())
        workbook.writestr("xl/workbook.xml", _workbook_xml([name for name, _ in sheets]))
        workbook.writestr("xl/_rels/workbook.xml.rels", _workbook_rels_xml(len(sheets)))
        workbook.writestr("xl/styles.xml", _styles_xml())
        for index, (_name, rows) in enumerate(sheets, start=1):
            workbook.writestr(f"xl/worksheets/sheet{index}.xml", _worksheet_xml(rows))


def _content_types_xml(sheet_count: int) -> str:
    sheet_overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{index}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for index in range(1, sheet_count + 1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        f"{sheet_overrides}</Types>"
    )


def _root_rels_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )


def _workbook_xml(sheet_names: list[str]) -> str:
    sheets_xml = "".join(
        f'<sheet name="{escape(name)}" sheetId="{index}" r:id="rId{index}"/>'
        for index, name in enumerate(sheet_names, start=1)
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{sheets_xml}</sheets></workbook>"
    )


def _workbook_rels_xml(sheet_count: int) -> str:
    sheet_rels = "".join(
        f'<Relationship Id="rId{index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{index}.xml"/>'
        for index in range(1, sheet_count + 1)
    )
    styles_id = sheet_count + 1
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{sheet_rels}"
        f'<Relationship Id="rId{styles_id}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/></Relationships>'
    )


def _styles_xml() -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<fonts count="1"><font><sz val="11"/><color theme="1"/><name val="Arial"/><family val="2"/></font></fonts>'
        '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
        '</styleSheet>'
    )


def _worksheet_xml(rows: list[list[object]]) -> str:
    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = "".join(_cell_xml(row_index, column_index, value) for column_index, value in enumerate(row, start=1))
        row_xml.append(f'<row r="{row_index}">{cells}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_xml)}</sheetData></worksheet>'
    )


def _cell_xml(row: int, column: int, value: object) -> str:
    ref = f"{_column_name(column)}{row}"
    if isinstance(value, int | float) and not isinstance(value, bool):
        return f'<c r="{ref}"><v>{value}</v></c>'
    text = escape(str(value))
    return f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>'


def _column_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name
