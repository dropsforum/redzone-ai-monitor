"""Geometry helpers for floor-contact red-zone entry."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

NormalizedPoint = tuple[float, float]
PixelPoint = tuple[float, float]
MaskPolygons = Sequence[Sequence[PixelPoint]] | Sequence[PixelPoint]

_MAX_RASTER_DIMENSION = 256


@dataclass(frozen=True)
class ZoneContact:
    foot_x: float
    foot_y: float
    inside: bool
    near: bool
    distance_px: float
    method: str = "footpoint"
    overlap_ratio: float = 0.0
    position_uncertain: bool = False


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


def classify_person_zone(
    x1: int,
    x2: int,
    y2: int,
    zone: Sequence[NormalizedPoint],
    frame_width: int,
    frame_height: int,
    warning_buffer: float,
    mask_polygons: MaskPolygons | None = None,
    mask_overlap_threshold: float = 0.02,
    bottom_clip_ratio: float = 0.98,
    mask_contact_tolerance: float = 0.01,
) -> ZoneContact:
    """Classify a person using their mask, with a cautious bbox fallback.

    ``mask_polygons`` accepts either one polygon or a sequence of polygons in
    frame pixel coordinates, matching the polygons produced by Ultralytics.
    The bounding box is used only for its floor-contact point and to detect a
    lower-body crop; rectangular overlap is never treated as body occupancy.
    """
    foot_contact = classify_foot_point(
        x1=x1,
        x2=x2,
        y2=y2,
        zone=zone,
        frame_width=frame_width,
        frame_height=frame_height,
        warning_buffer=warning_buffer,
    )
    normalized_masks = _normalize_mask_polygons(
        mask_polygons,
        frame_width,
        frame_height,
    )
    if normalized_masks:
        raster_width, raster_height = _raster_dimensions(
            frame_width,
            frame_height,
        )
        person_pixels = _rasterize_polygons(
            normalized_masks,
            raster_width,
            raster_height,
        )
        if person_pixels:
            zone_pixels = _rasterize_polygons(
                [zone],
                raster_width,
                raster_height,
            )
            overlap_pixels = person_pixels.intersection(zone_pixels)
            overlap_ratio = len(overlap_pixels) / len(person_pixels)
            required_overlap = max(0.0, min(1.0, mask_overlap_threshold))
            inside = bool(overlap_pixels) and overlap_ratio >= required_overlap
            pixel_polygon = [
                (x * frame_width, y * frame_height)
                for x, y in zone
            ]
            distance_px = _raster_to_polygon_distance(
                person_pixels,
                pixel_polygon,
                raster_width,
                raster_height,
                frame_width,
                frame_height,
            )
            shortest_side = min(frame_width, frame_height)
            contact_distance_px = (
                max(0.0, mask_contact_tolerance) * shortest_side
            )
            warning_distance_px = max(
                contact_distance_px,
                max(0.0, warning_buffer) * shortest_side,
            )
            inside = inside or (
                not overlap_pixels and distance_px <= contact_distance_px
            )
            return ZoneContact(
                foot_x=foot_contact.foot_x,
                foot_y=foot_contact.foot_y,
                inside=inside,
                near=(
                    bool(overlap_pixels)
                    or distance_px <= warning_distance_px
                ),
                distance_px=distance_px,
                method="mask",
                overlap_ratio=overlap_ratio,
            )

    if _is_bottom_cropped(y2, frame_height, bottom_clip_ratio):
        return ZoneContact(
            foot_x=foot_contact.foot_x,
            foot_y=foot_contact.foot_y,
            inside=foot_contact.inside,
            near=True,
            distance_px=foot_contact.distance_px,
            method="bottom-cropped",
            position_uncertain=True,
        )
    return foot_contact


def _normalize_mask_polygons(
    mask_polygons: MaskPolygons | None,
    frame_width: int,
    frame_height: int,
) -> list[list[NormalizedPoint]]:
    if mask_polygons is None or frame_width <= 0 or frame_height <= 0:
        return []
    try:
        first = mask_polygons[0]
    except (IndexError, KeyError, TypeError):
        return []

    candidates: Sequence[Sequence[PixelPoint]]
    if _coerce_point(first) is not None:
        candidates = [mask_polygons]  # type: ignore[list-item]
    else:
        candidates = mask_polygons  # type: ignore[assignment]

    normalized: list[list[NormalizedPoint]] = []
    for candidate in candidates:
        polygon: list[NormalizedPoint] = []
        for value in candidate:
            point = _coerce_point(value)
            if point is None:
                continue
            polygon.append(
                (point[0] / frame_width, point[1] / frame_height)
            )
        if len(polygon) >= 3 and abs(_polygon_area(polygon)) > 1e-9:
            normalized.append(polygon)
    return normalized


def _coerce_point(value: object) -> PixelPoint | None:
    try:
        if len(value) != 2:  # type: ignore[arg-type]
            return None
        x = float(value[0])  # type: ignore[index]
        y = float(value[1])  # type: ignore[index]
    except (IndexError, TypeError, ValueError):
        return None
    if not math.isfinite(x) or not math.isfinite(y):
        return None
    return x, y


def _polygon_area(polygon: Sequence[NormalizedPoint]) -> float:
    return sum(
        polygon[index - 1][0] * polygon[index][1]
        - polygon[index][0] * polygon[index - 1][1]
        for index in range(len(polygon))
    ) / 2.0


def _raster_dimensions(frame_width: int, frame_height: int) -> tuple[int, int]:
    largest_dimension = max(1, frame_width, frame_height)
    scale = min(1.0, _MAX_RASTER_DIMENSION / largest_dimension)
    return (
        max(1, round(frame_width * scale)),
        max(1, round(frame_height * scale)),
    )


def _rasterize_polygons(
    polygons: Sequence[Sequence[NormalizedPoint]],
    width: int,
    height: int,
) -> set[int]:
    pixels: set[int] = set()
    for polygon in polygons:
        if len(polygon) < 3:
            continue
        minimum_y = min(point[1] for point in polygon)
        maximum_y = max(point[1] for point in polygon)
        first_row = max(0, math.ceil(minimum_y * height - 0.5))
        last_row = min(height - 1, math.floor(maximum_y * height - 0.5))
        for row in range(first_row, last_row + 1):
            sample_y = (row + 0.5) / height
            intersections: list[float] = []
            previous_x, previous_y = polygon[-1]
            for current_x, current_y in polygon:
                if (current_y > sample_y) != (previous_y > sample_y):
                    intersections.append(
                        current_x
                        + (sample_y - current_y)
                        * (previous_x - current_x)
                        / (previous_y - current_y)
                    )
                previous_x, previous_y = current_x, current_y
            intersections.sort()
            for index in range(0, len(intersections) - 1, 2):
                left = intersections[index]
                right = intersections[index + 1]
                first_column = max(0, math.ceil(left * width - 0.5))
                last_column = min(width - 1, math.floor(right * width - 0.5))
                for column in range(first_column, last_column + 1):
                    pixels.add(row * width + column)
    return pixels


def _raster_to_polygon_distance(
    pixels: set[int],
    polygon: Sequence[tuple[float, float]],
    raster_width: int,
    raster_height: int,
    output_width: float = 1.0,
    output_height: float = 1.0,
) -> float:
    if not pixels or len(polygon) < 2:
        return math.inf
    return min(
        _point_to_polygon_distance(
            (
                ((pixel % raster_width) + 0.5)
                / raster_width
                * output_width,
                ((pixel // raster_width) + 0.5)
                / raster_height
                * output_height,
            ),
            polygon,
        )
        for pixel in pixels
    )


def _is_bottom_cropped(
    y2: int,
    frame_height: int,
    bottom_clip_ratio: float = 0.98,
) -> bool:
    if frame_height <= 0:
        return False
    threshold = max(0.0, min(1.0, bottom_clip_ratio))
    return y2 >= frame_height * threshold


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
