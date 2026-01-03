import { Point } from '../components/ZoneEditor';
import { Detection } from './yolo-detector';

/**
 * Checks if a point (x, y) is inside a polygon defined by an array of points.
 * Uses the Ray-Casting algorithm.
 */
export function isPointInPolygon(point: Point, polygon: Point[]): boolean {
  if (polygon.length < 3) return false;

  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const xi = polygon[i].x, yi = polygon[i].y;
    const xj = polygon[j].x, yj = polygon[j].y;

    const intersect = ((yi > point.y) !== (yj > point.y)) &&
      (point.x < (xj - xi) * (point.y - yi) / (yj - yi) + xi);
    
    if (intersect) inside = !inside;
  }

  return inside;
}

/**
 * Calculate the distance from a point to a line segment.
 */
function pointToLineDistance(px: number, py: number, x1: number, y1: number, x2: number, y2: number): number {
  const A = px - x1;
  const B = py - y1;
  const C = x2 - x1;
  const D = y2 - y1;

  const dot = A * C + B * D;
  const lenSq = C * C + D * D;
  let param = -1;

  if (lenSq !== 0) param = dot / lenSq;

  let xx: number, yy: number;

  if (param < 0) {
    xx = x1;
    yy = y1;
  } else if (param > 1) {
    xx = x2;
    yy = y2;
  } else {
    xx = x1 + param * C;
    yy = y1 + param * D;
  }

  const dx = px - xx;
  const dy = py - yy;
  return Math.sqrt(dx * dx + dy * dy);
}

/**
 * Calculate the minimum distance from a point to the nearest edge of a polygon.
 * Returns the distance in normalized coordinates (0-1 range).
 */
export function distanceToZoneEdge(point: Point, polygon: Point[]): number {
  if (polygon.length < 3) return Infinity;

  let minDistance = Infinity;

  for (let i = 0; i < polygon.length; i++) {
    const j = (i + 1) % polygon.length;
    const dist = pointToLineDistance(
      point.x, point.y,
      polygon[i].x, polygon[i].y,
      polygon[j].x, polygon[j].y
    );
    minDistance = Math.min(minDistance, dist);
  }

  return minDistance;
}

/**
 * Checks if any person detections are inside the monitoring zone.
 * @param strict If true, triggers if ANY part of the bounding box enters the zone. 
 *               If false, triggers only if the CENTER enters the zone.
 */
export function isPersonInZone(detection: Detection, zone: Point[], imageWidth: number, imageHeight: number, strict: boolean = false): boolean {
  if (zone.length < 3) return false;

  // Check center point
  const centerX = (detection.x1 + detection.x2) / 2 / imageWidth;
  const centerY = (detection.y1 + detection.y2) / 2 / imageHeight;
  
  if (isPointInPolygon({ x: centerX, y: centerY }, zone)) {
    return true;
  }

  // If not strict, we only care about the center point
  if (!strict) return false;

  // Check all four corners for strict mode
  const corners = [
    { x: detection.x1 / imageWidth, y: detection.y1 / imageHeight }, // top-left
    { x: detection.x2 / imageWidth, y: detection.y1 / imageHeight }, // top-right
    { x: detection.x2 / imageWidth, y: detection.y2 / imageHeight }, // bottom-right
    { x: detection.x1 / imageWidth, y: detection.y2 / imageHeight }, // bottom-left
  ];

  return corners.some(corner => isPointInPolygon(corner, zone));
}

/**
 * Checks if a person is partially in or near the zone (for yellow traffic light).
 * Returns true if any part of the bounding box intersects the zone but center is not in,
 * OR if the person is within the proximity threshold of the zone edge.
 */
export function isPersonNearZone(detection: Detection, zone: Point[], imageWidth: number, imageHeight: number, proximityThreshold: number = 0.1): boolean {
  if (zone.length < 3) return false;

  // Calculate center point in normalized coordinates (0-1)
  const centerX = (detection.x1 + detection.x2) / 2 / imageWidth;
  const centerY = (detection.y1 + detection.y2) / 2 / imageHeight;
  const centerPoint = { x: centerX, y: centerY };

  // Don't trigger yellow if center is in zone (red takes precedence)
  if (isPointInPolygon(centerPoint, zone)) {
    return false;
  }

  // Check if any corner of the bounding box is in the zone (partial overlap = yellow)
  const corners = [
    { x: detection.x1 / imageWidth, y: detection.y1 / imageHeight }, // top-left
    { x: detection.x2 / imageWidth, y: detection.y1 / imageHeight }, // top-right
    { x: detection.x2 / imageWidth, y: detection.y2 / imageHeight }, // bottom-right
    { x: detection.x1 / imageWidth, y: detection.y2 / imageHeight }, // bottom-left
  ];

  if (corners.some(corner => isPointInPolygon(corner, zone))) {
    return true; // Partially in zone = yellow
  }

  // Also check if center point is near the zone edge
  const distance = distanceToZoneEdge(centerPoint, zone);
  return distance <= proximityThreshold;
}
