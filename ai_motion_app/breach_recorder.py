"""Persistent red-zone session, person-event, and report recorder."""

from __future__ import annotations

import csv
import json
import time
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Literal
from xml.sax.saxutils import escape

from .platform_utils import get_app_data_dir
from .session_store import SessionStore

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


@dataclass
class PersonBreachEvent:
    track_id: int
    start: float
    end: float
    max_confidence: float


class BreachRecorder:
    def __init__(self, database_path: Path | None = None):
        db_path = database_path or (get_app_data_dir() / "monitoring.sqlite3")
        self.store = SessionStore(db_path)
        self.completed: list[BreachSegment] = []
        self.active: BreachSegment | None = None
        self.completed_people: list[PersonBreachEvent] = []
        self.active_people: dict[int, PersonBreachEvent] = {}
        self._active_segment_row_id: int | None = None
        self._active_person_row_ids: dict[int, int] = {}
        self.session_id: str | None = self.store.latest_session_id()
        self.metadata: dict[str, Any] = {}
        self.running = False
        self._load_latest_session()

    def start(
        self,
        now: float | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        if self.running:
            return
        now = time.time() if now is None else now
        self.completed.clear()
        self.completed_people.clear()
        self.active_people.clear()
        self._active_person_row_ids.clear()
        self.metadata = dict(metadata or {})
        self.session_id = str(uuid.uuid4())
        self.store.create_session(self.session_id, now, self.metadata)
        self.running = True
        self.active = BreachSegment(now, now, "clear")
        self._active_segment_row_id = self.store.start_state_segment(
            self.session_id,
            "clear",
            now,
        )

    def stop(self, now: float | None = None):
        if not self.running:
            return
        now = time.time() if now is None else now
        self._close_active(now)
        for track_id in list(self.active_people):
            self.end_person_breach(track_id, now)
        if self.session_id is not None:
            self.store.finish_session(self.session_id, now)
        self.active = None
        self._active_segment_row_id = None
        self.running = False

    def reset(self):
        if self.running:
            self.stop()
        self.completed.clear()
        self.completed_people.clear()
        self.active_people.clear()
        self.active = None
        self._active_segment_row_id = None
        self._active_person_row_ids.clear()
        self.session_id = None
        self.metadata = {}
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
        if self.session_id is not None:
            self._active_segment_row_id = self.store.start_state_segment(
                self.session_id,
                next_state,
                now,
            )

    def start_person_breach(
        self,
        track_id: int,
        start: float,
        confidence: float,
    ) -> None:
        if not self.running or self.session_id is None:
            return
        if track_id in self.active_people:
            self.update_person_confidence(track_id, confidence)
            return
        event = PersonBreachEvent(track_id, start, start, confidence)
        self.active_people[track_id] = event
        self._active_person_row_ids[track_id] = self.store.start_person_event(
            self.session_id,
            track_id,
            start,
            confidence,
        )

    def update_person_confidence(self, track_id: int, confidence: float) -> None:
        event = self.active_people.get(track_id)
        if event is None:
            return
        event.max_confidence = max(event.max_confidence, confidence)
        row_id = self._active_person_row_ids.get(track_id)
        if row_id is not None:
            self.store.update_person_confidence(row_id, confidence)

    def end_person_breach(
        self,
        track_id: int,
        end: float,
        confidence: float | None = None,
    ) -> None:
        event = self.active_people.pop(track_id, None)
        row_id = self._active_person_row_ids.pop(track_id, None)
        if event is None:
            return
        event.end = max(event.start, end)
        if confidence is not None:
            event.max_confidence = max(event.max_confidence, confidence)
        self.completed_people.append(event)
        if row_id is not None:
            self.store.close_person_event(
                row_id,
                event.end,
                event.max_confidence,
            )

    def heartbeat(
        self,
        now: float | None = None,
        health: dict[str, Any] | None = None,
    ) -> None:
        if not self.running or self.session_id is None:
            return
        now = time.time() if now is None else now
        if self.active is not None:
            self.active.end = max(self.active.end, now)
        self.store.heartbeat(self.session_id, now, health)

    def segments(self, now: float | None = None) -> list[BreachSegment]:
        now = time.time() if now is None else now
        segments = list(self.completed)
        if self.running and self.active is not None:
            segments.append(BreachSegment(self.active.start, max(self.active.end, now), self.active.state))
        return [segment for segment in segments if segment.end > segment.start]

    def person_events(self, now: float | None = None) -> list[PersonBreachEvent]:
        now = time.time() if now is None else now
        events = list(self.completed_people)
        events.extend(
            PersonBreachEvent(
                event.track_id,
                event.start,
                max(event.end, now),
                event.max_confidence,
            )
            for event in self.active_people.values()
        )
        return [
            event
            for event in sorted(events, key=lambda item: item.start)
            if event.end > event.start
        ]

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
            "person_breach_count": len(self.person_events()),
            "unique_people": len({event.track_id for event in self.person_events()}),
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
            ["person_breach_event_count", int(summary["person_breach_count"])],
            ["unique_tracked_people", int(summary["unique_people"])],
        ]
        people_rows = [
            [
                "track_id",
                "start_datetime",
                "end_datetime",
                "start_iso",
                "end_iso",
                "duration_seconds",
                "max_confidence",
            ],
            *[
                [
                    event.track_id,
                    _local_datetime(event.start),
                    _local_datetime(event.end),
                    _iso_datetime(event.start),
                    _iso_datetime(event.end),
                    round(event.end - event.start, 2),
                    round(event.max_confidence, 4),
                ]
                for event in self.person_events()
            ],
        ]
        metadata_rows = self._metadata_rows()
        _write_xlsx(
            path,
            [
                ("Records", records_rows),
                ("Person Breaches", people_rows),
                ("Aggregated Results", aggregated_rows),
                ("Overall Metrics", metrics_rows),
                ("Session Metadata", metadata_rows),
            ],
        )

    def _close_active(self, now: float):
        if self.active is None:
            return
        self.completed.append(BreachSegment(self.active.start, max(self.active.start, now), self.active.state))
        if self._active_segment_row_id is not None:
            self.store.close_state_segment(self._active_segment_row_id, now)
            self._active_segment_row_id = None

    def _load_latest_session(self) -> None:
        if self.session_id is None:
            return
        self.metadata = self.store.session(self.session_id)
        self.completed = [
            BreachSegment(
                float(row["start_time"]),
                float(row["end_time"] or row["start_time"]),
                str(row["state"]),
            )
            for row in self.store.state_segments(self.session_id)
        ]
        self.completed_people = [
            PersonBreachEvent(
                int(row["track_id"]),
                float(row["start_time"]),
                float(row["end_time"] or row["start_time"]),
                float(row["max_confidence"]),
            )
            for row in self.store.person_events(self.session_id)
        ]

    def _metadata_rows(self) -> list[list[object]]:
        metadata = self.store.session(self.session_id) if self.session_id else self.metadata
        health = self.store.health_summary(self.session_id) if self.session_id else {}
        rows: list[list[object]] = [["field", "value"]]
        preferred = [
            "id",
            "status",
            "start_time",
            "end_time",
            "last_heartbeat",
            "source_type",
            "model_name",
            "model_version",
            "detector_backend",
        ]
        for field in preferred:
            value = metadata.get(field, "")
            if field.endswith("_time") or field == "last_heartbeat":
                value = _local_datetime(float(value)) if value else ""
            rows.append([field, value])
        rows.extend([
            ["zone", json.dumps(metadata.get("zone", []), separators=(",", ":"))],
            ["settings", json.dumps(metadata.get("settings", {}), separators=(",", ":"))],
        ])
        for field in sorted(health):
            rows.append([f"inference_{field}", health[field]])
        return rows

    def close(self) -> None:
        self.store.close()


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
