"""Geometry helpers for floor-contact red-zone entry."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

NormalizedPoint = tuple[float, float]


@dataclass(frozen=True)
class ZoneContact:
    foot_x: float
    foot_y: float
    inside: bool
    near: bool
    distance_px: float


def classify_foot_point(
    x1: int,
    x2: int,
    y2: int,
    zone: Sequence[NormalizedPoint],
    frame_width: int,
    frame_height: int,
    warning_buffer: float,
) -> ZoneContact:
    foot_x = (x1 + x2) / 2.0
    foot_y = float(y2)
    pixel_polygon = [
        (x * frame_width, y * frame_height)
        for x, y in zone
    ]
    normalized_point = (
        foot_x / max(1, frame_width),
        foot_y / max(1, frame_height),
    )
    normalized_distance = _point_to_polygon_distance(normalized_point, zone)
    distance_px = _point_to_polygon_distance((foot_x, foot_y), pixel_polygon)
    inside = (
        _point_in_polygon(normalized_point, zone)
        or normalized_distance <= 1e-9
    )
    return ZoneContact(
        foot_x=foot_x,
        foot_y=foot_y,
        inside=inside,
        near=inside or normalized_distance <= max(0.0, warning_buffer),
        distance_px=distance_px,
    )


def _point_in_polygon(
    point: tuple[float, float],
    polygon: Sequence[tuple[float, float]],
) -> bool:
    if len(polygon) < 3:
        return False
    x, y = point
    inside = False
    previous_x, previous_y = polygon[-1]
    for current_x, current_y in polygon:
        if (current_y > y) != (previous_y > y):
            crossing_x = (
                (previous_x - current_x)
                * (y - current_y)
                / (previous_y - current_y)
                + current_x
            )
            if x < crossing_x:
                inside = not inside
        previous_x, previous_y = current_x, current_y
    return inside


def _point_to_polygon_distance(
    point: tuple[float, float],
    polygon: Sequence[tuple[float, float]],
) -> float:
    if len(polygon) < 2:
        return math.inf
    return min(
        _point_to_segment_distance(point, polygon[index - 1], polygon[index])
        for index in range(len(polygon))
    )


def _point_to_segment_distance(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    px, py = point
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    length_squared = dx * dx + dy * dy
    if length_squared <= 0:
        return math.hypot(px - sx, py - sy)
    projection = ((px - sx) * dx + (py - sy) * dy) / length_squared
    projection = max(0.0, min(1.0, projection))
    closest_x = sx + projection * dx
    closest_y = sy + projection * dy
    return math.hypot(px - closest_x, py - closest_y)
