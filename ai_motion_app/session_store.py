"""SQLite persistence for native monitoring sessions."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable


class SessionStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        if str(self.path) != ":memory:":
            self.connection.execute("PRAGMA journal_mode = WAL")
        self._create_schema()
        self.recover_unfinished_sessions()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS monitoring_sessions (
                id TEXT PRIMARY KEY,
                start_time REAL NOT NULL,
                end_time REAL,
                last_heartbeat REAL NOT NULL,
                source_type TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                detector_backend TEXT NOT NULL,
                zone_json TEXT NOT NULL,
                settings_json TEXT NOT NULL,
                status TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS state_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES monitoring_sessions(id),
                state TEXT NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL
            );

            CREATE TABLE IF NOT EXISTS person_breach_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES monitoring_sessions(id),
                track_id INTEGER NOT NULL,
                start_time REAL NOT NULL,
                end_time REAL,
                max_confidence REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS inference_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES monitoring_sessions(id),
                recorded_at REAL NOT NULL,
                observed_fps REAL NOT NULL,
                preprocess_ms REAL NOT NULL,
                inference_ms REAL NOT NULL,
                postprocess_ms REAL NOT NULL,
                total_ms REAL NOT NULL,
                dropped_requests INTEGER NOT NULL,
                detector_errors INTEGER NOT NULL,
                backend TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS state_segments_session_idx
                ON state_segments(session_id, start_time);
            CREATE INDEX IF NOT EXISTS person_events_session_idx
                ON person_breach_events(session_id, start_time);
            CREATE INDEX IF NOT EXISTS inference_health_session_idx
                ON inference_health(session_id, recorded_at);
            """
        )
        self.connection.commit()

    def recover_unfinished_sessions(self) -> list[str]:
        recovered: list[str] = []
        rows = self.connection.execute(
            "SELECT id, start_time, last_heartbeat FROM monitoring_sessions WHERE status = 'active'"
        ).fetchall()
        for row in rows:
            session_id = str(row["id"])
            end_time = max(float(row["start_time"]), float(row["last_heartbeat"]))
            self.connection.execute(
                """
                UPDATE state_segments
                SET end_time = ?
                WHERE session_id = ? AND end_time IS NULL
                """,
                (end_time, session_id),
            )
            self.connection.execute(
                """
                UPDATE person_breach_events
                SET end_time = ?
                WHERE session_id = ? AND end_time IS NULL
                """,
                (end_time, session_id),
            )
            self.connection.execute(
                """
                UPDATE monitoring_sessions
                SET end_time = ?, status = 'recovered'
                WHERE id = ?
                """,
                (end_time, session_id),
            )
            recovered.append(session_id)
        if recovered:
            self.connection.commit()
        return recovered

    def create_session(self, session_id: str, start_time: float, metadata: dict[str, Any]) -> None:
        self.connection.execute(
            """
            INSERT INTO monitoring_sessions (
                id, start_time, end_time, last_heartbeat, source_type,
                model_name, model_version, detector_backend, zone_json,
                settings_json, status
            ) VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            (
                session_id,
                start_time,
                start_time,
                str(metadata.get("source_type", "unknown")),
                str(metadata.get("model_name", "unknown")),
                str(metadata.get("model_version", "unknown")),
                str(metadata.get("detector_backend", "unknown")),
                json.dumps(metadata.get("zone", []), separators=(",", ":")),
                json.dumps(metadata.get("settings", {}), separators=(",", ":")),
            ),
        )
        self.connection.commit()

    def heartbeat(
        self,
        session_id: str,
        now: float,
        health: dict[str, Any] | None = None,
    ) -> None:
        self.connection.execute(
            "UPDATE monitoring_sessions SET last_heartbeat = ? WHERE id = ? AND status = 'active'",
            (now, session_id),
        )
        if health is not None:
            self.connection.execute(
                """
                INSERT INTO inference_health (
                    session_id, recorded_at, observed_fps, preprocess_ms,
                    inference_ms, postprocess_ms, total_ms, dropped_requests,
                    detector_errors, backend
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    now,
                    float(health.get("observed_fps", 0.0)),
                    float(health.get("preprocess_ms", 0.0)),
                    float(health.get("inference_ms", 0.0)),
                    float(health.get("postprocess_ms", 0.0)),
                    float(health.get("total_ms", 0.0)),
                    int(health.get("dropped_requests", 0)),
                    int(health.get("detector_errors", 0)),
                    str(health.get("backend", "unknown")),
                ),
            )
        self.connection.commit()

    def finish_session(self, session_id: str, end_time: float) -> None:
        self.connection.execute(
            """
            UPDATE state_segments
            SET end_time = ?
            WHERE session_id = ? AND end_time IS NULL
            """,
            (end_time, session_id),
        )
        self.connection.execute(
            """
            UPDATE person_breach_events
            SET end_time = ?
            WHERE session_id = ? AND end_time IS NULL
            """,
            (end_time, session_id),
        )
        self.connection.execute(
            """
            UPDATE monitoring_sessions
            SET end_time = ?, last_heartbeat = ?, status = 'completed'
            WHERE id = ?
            """,
            (end_time, end_time, session_id),
        )
        self.connection.commit()

    def start_state_segment(self, session_id: str, state: str, start_time: float) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO state_segments(session_id, state, start_time, end_time)
            VALUES (?, ?, ?, NULL)
            """,
            (session_id, state, start_time),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def close_state_segment(self, row_id: int, end_time: float) -> None:
        self.connection.execute(
            "UPDATE state_segments SET end_time = ? WHERE id = ?",
            (end_time, row_id),
        )
        self.connection.commit()

    def start_person_event(
        self,
        session_id: str,
        track_id: int,
        start_time: float,
        max_confidence: float,
    ) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO person_breach_events(
                session_id, track_id, start_time, end_time, max_confidence
            ) VALUES (?, ?, ?, NULL, ?)
            """,
            (session_id, track_id, start_time, max_confidence),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def update_person_confidence(self, row_id: int, confidence: float) -> None:
        self.connection.execute(
            """
            UPDATE person_breach_events
            SET max_confidence = MAX(max_confidence, ?)
            WHERE id = ?
            """,
            (confidence, row_id),
        )
        self.connection.commit()

    def close_person_event(self, row_id: int, end_time: float, max_confidence: float) -> None:
        self.connection.execute(
            """
            UPDATE person_breach_events
            SET end_time = ?, max_confidence = MAX(max_confidence, ?)
            WHERE id = ?
            """,
            (end_time, max_confidence, row_id),
        )
        self.connection.commit()

    def latest_session_id(self) -> str | None:
        row = self.connection.execute(
            """
            SELECT id FROM monitoring_sessions
            ORDER BY start_time DESC LIMIT 1
            """
        ).fetchone()
        return str(row["id"]) if row else None

    def session(self, session_id: str) -> dict[str, Any]:
        row = self.connection.execute(
            "SELECT * FROM monitoring_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if row is None:
            return {}
        data = dict(row)
        data["zone"] = json.loads(data.pop("zone_json"))
        data["settings"] = json.loads(data.pop("settings_json"))
        return data

    def state_segments(self, session_id: str) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT id, state, start_time, end_time
            FROM state_segments
            WHERE session_id = ?
            ORDER BY start_time
            """,
            (session_id,),
        )

    def person_events(self, session_id: str) -> list[dict[str, Any]]:
        return self._rows(
            """
            SELECT id, track_id, start_time, end_time, max_confidence
            FROM person_breach_events
            WHERE session_id = ?
            ORDER BY start_time
            """,
            (session_id,),
        )

    def health_summary(self, session_id: str) -> dict[str, Any]:
        row = self.connection.execute(
            """
            SELECT
                COUNT(*) AS sample_count,
                AVG(observed_fps) AS average_fps,
                AVG(preprocess_ms) AS average_preprocess_ms,
                AVG(inference_ms) AS average_inference_ms,
                AVG(postprocess_ms) AS average_postprocess_ms,
                AVG(total_ms) AS average_total_ms,
                MAX(dropped_requests) AS dropped_requests,
                MAX(detector_errors) AS detector_errors,
                MAX(backend) AS backend
            FROM inference_health
            WHERE session_id = ?
            """,
            (session_id,),
        ).fetchone()
        if row is None:
            return {}
        return {
            key: (0 if value is None and key != "backend" else value)
            for key, value in dict(row).items()
        }

    def _rows(self, query: str, parameters: Iterable[Any]) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.connection.execute(query, tuple(parameters)).fetchall()
        ]

    def close(self) -> None:
        self.connection.close()
