import { hasCoordinates } from './incidentFilters.js';

const radians = (degrees) => degrees * Math.PI / 180;
const validPoint = (point) => hasCoordinates(point) && Math.abs(point.latitude) <= 90 && Math.abs(point.longitude) <= 180;

export function distanceKm(start, end) {
  const latitude = radians(end.latitude - start.latitude);
  const longitude = radians(end.longitude - start.longitude);
  const a = Math.sin(latitude / 2) ** 2
    + Math.cos(radians(start.latitude)) * Math.cos(radians(end.latitude)) * Math.sin(longitude / 2) ** 2;
  return 6371.0088 * 2 * Math.asin(Math.sqrt(Math.min(1, Math.max(0, a))));
}

export function nearestDestinations(incidents, origin, limit = 5) {
  if (!validPoint(origin)) throw new Error('Link chưa có tọa độ vị trí xuất phát hợp lệ.');
  const candidates = incidents
    .filter((item) => validPoint(item) && !['resolved', 'rejected'].includes(item.status))
    .map((item) => ({ ...item, distance_km: distanceKm(origin, item) }))
    .sort((a, b) => a.distance_km - b.distance_km || a.id - b.id);
  const seen = new Set();
  return candidates.filter((item) => {
    const key = `${item.latitude.toFixed(6)},${item.longitude.toFixed(6)}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  }).slice(0, limit);
}

export function directionsURL(origin, destination) {
  const params = new URLSearchParams({ api: '1', origin: `${origin.latitude},${origin.longitude}`,
    destination: `${destination.latitude},${destination.longitude}`, travelmode: 'driving' });
  return `https://www.google.com/maps/dir/?${params}`;
}

export const routeColors = ['#2563EB', '#9333EA', '#D97706', '#059669', '#DB2777'];
