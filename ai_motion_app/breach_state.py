"""Temporal red-zone state derived from tracked person observations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

TrafficState = Literal["green", "yellow", "red"]


@dataclass(frozen=True)
class TrackObservation:
    track_id: int
    inside: bool
    near: bool
    confidence: float


@dataclass(frozen=True)
class PersonEventStarted:
    track_id: int
    start: float
    max_confidence: float


@dataclass(frozen=True)
class PersonEventEnded:
    track_id: int
    end: float
    max_confidence: float


@dataclass(frozen=True)
class BreachDecision:
    traffic: TrafficState
    is_breach: bool
    entered_breach: bool
    exited_breach: bool
    active_track_ids: tuple[int, ...]
    pending_track_ids: tuple[int, ...]
    started_events: tuple[PersonEventStarted, ...] = ()
    ended_events: tuple[PersonEventEnded, ...] = ()


@dataclass
class _TrackState:
    track_id: int
    first_inside_at: float | None = None
    last_inside_at: float | None = None
    last_seen_at: float = 0.0
    confirmed: bool = False
    event_max_confidence: float = 0.0


class BreachStateMachine:
    """Apply confirmation and grace periods to tracked foot-point observations."""

    def __init__(
        self,
        entry_confirm_ms: int = 300,
        exit_grace_ms: int = 750,
        tracker_max_gap_ms: int = 750,
    ):
        self.entry_confirm_seconds = max(0.0, entry_confirm_ms / 1000.0)
        self.exit_grace_seconds = max(0.0, exit_grace_ms / 1000.0)
        self.tracker_max_gap_seconds = max(0.0, tracker_max_gap_ms / 1000.0)
        self._tracks: dict[int, _TrackState] = {}
        self._is_breach = False

    def update(
        self,
        observations: Sequence[TrackObservation],
        now: float,
    ) -> BreachDecision:
        started: list[PersonEventStarted] = []
        ended: list[PersonEventEnded] = []
        seen_ids: set[int] = set()
        near_seen = False

        for observation in observations:
            seen_ids.add(observation.track_id)
            near_seen = near_seen or observation.near
            track = self._tracks.setdefault(
                observation.track_id,
                _TrackState(track_id=observation.track_id),
            )
            track.last_seen_at = now

            if observation.inside:
                if track.first_inside_at is None:
                    track.first_inside_at = now
                    track.event_max_confidence = observation.confidence
                else:
                    track.event_max_confidence = max(
                        track.event_max_confidence,
                        observation.confidence,
                    )
                track.last_inside_at = now

                if (
                    not track.confirmed
                    and now - track.first_inside_at >= self.entry_confirm_seconds
                ):
                    track.confirmed = True
                    started.append(PersonEventStarted(
                        track_id=track.track_id,
                        start=track.first_inside_at,
                        max_confidence=track.event_max_confidence,
                    ))
            elif not track.confirmed:
                track.first_inside_at = None
                track.last_inside_at = None
                track.event_max_confidence = 0.0

        for track_id, track in list(self._tracks.items()):
            if track.confirmed and track.last_inside_at is not None:
                grace_end = track.last_inside_at + self.exit_grace_seconds
                if now > grace_end:
                    ended.append(PersonEventEnded(
                        track_id=track.track_id,
                        end=grace_end,
                        max_confidence=track.event_max_confidence,
                    ))
                    track.confirmed = False
                    track.first_inside_at = None
                    track.last_inside_at = None
                    track.event_max_confidence = 0.0

            if (
                not track.confirmed
                and now - track.last_seen_at > self.tracker_max_gap_seconds
            ):
                del self._tracks[track_id]

        active_ids = tuple(sorted(
            track.track_id for track in self._tracks.values() if track.confirmed
        ))
        pending_ids = tuple(sorted(
            track.track_id
            for track in self._tracks.values()
            if not track.confirmed and track.first_inside_at is not None
        ))
        is_breach = bool(active_ids)
        entered_breach = is_breach and not self._is_breach
        exited_breach = self._is_breach and not is_breach
        self._is_breach = is_breach

        if is_breach:
            traffic: TrafficState = "red"
        elif pending_ids or near_seen:
            traffic = "yellow"
        else:
            traffic = "green"

        return BreachDecision(
            traffic=traffic,
            is_breach=is_breach,
            entered_breach=entered_breach,
            exited_breach=exited_breach,
            active_track_ids=active_ids,
            pending_track_ids=pending_ids,
            started_events=tuple(started),
            ended_events=tuple(ended),
        )

    def reset(self, now: float) -> BreachDecision:
        """End active person events immediately and clear all temporal state."""
        ended = tuple(
            PersonEventEnded(
                track_id=track.track_id,
                end=now,
                max_confidence=track.event_max_confidence,
            )
            for track in self._tracks.values()
            if track.confirmed
        )
        was_breach = self._is_breach
        self._tracks.clear()
        self._is_breach = False
        return BreachDecision(
            traffic="green",
            is_breach=False,
            entered_breach=False,
            exited_breach=was_breach,
            active_track_ids=(),
            pending_track_ids=(),
            ended_events=ended,
        )
