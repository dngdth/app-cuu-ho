import assert from 'node:assert/strict';
import test from 'node:test';
import { directionsURL, distanceKm, nearestDestinations } from '../src/utils/nearbyRoutes.js';
import { extractCoordsFromURL } from '../src/utils/mapUtils.js';

const origin = { latitude: 16.46, longitude: 107.58 };
const incident = (id, offset, extra = {}) => ({ id, latitude: origin.latitude + offset,
  longitude: origin.longitude, status: 'unverified', ...extra });

test('nearest five are ordered by geographic distance regardless of input order', () => {
  const rows = [7, 3, 6, 1, 5, 2, 4].map((id) => incident(id, id * 0.01));
  const result = nearestDestinations(rows, origin);
  assert.deepEqual(result.map((row) => row.id), [1, 2, 3, 4, 5]);
  assert.ok(Math.abs(result[0].distance_km - 1.11195) < 0.001);
  assert.deepEqual(rows.map((row) => row.id), [7, 3, 6, 1, 5, 2, 4]);
});

test('missing/invalid coordinates, finished requests and repeated locations are excluded', () => {
  const rows = [incident(1, 0.01), incident(2, 0.01), incident(3, 0.02),
    incident(4, 0, { latitude: null }), incident(5, 0, { longitude: 181 }),
    incident(6, 0, { status: 'resolved' }), incident(7, 0, { status: 'rejected' })];
  assert.deepEqual(nearestDestinations(rows, origin).map((row) => row.id), [1, 3]);
  assert.deepEqual(nearestDestinations([], origin), []);
  assert.throws(() => nearestDestinations(rows, { latitude: null, longitude: 0 }));
});

test('distances handle longitude wrapping and poles', () => {
  const distance = distanceKm({ latitude: 0, longitude: 179.9 }, { latitude: 0, longitude: -179.9 });
  assert.ok(distance > 22 && distance < 23);
  assert.ok(Number.isFinite(distanceKm({ latitude: 90, longitude: 0 }, { latitude: -90, longitude: 0 })));
});

test('explicit Google Maps pins become the origin and directions retain latitude/longitude order', () => {
  assert.deepEqual(extractCoordsFromURL('https://maps.google.com/?q=16.46,107.58'), { lat: 16.46, lng: 107.58 });
  assert.equal(extractCoordsFromURL('https://www.google.com/maps/@16.46,107.58,14z'), null);
  assert.equal(extractCoordsFromURL('https://maps.app.goo.gl/E2EOrigin'), null);
  const url = new URL(directionsURL(origin, incident(1, 0.01)));
  assert.equal(url.origin, 'https://www.google.com');
  assert.equal(url.searchParams.get('origin'), '16.46,107.58');
  const [latitude, longitude] = url.searchParams.get('destination').split(',').map(Number);
  assert.ok(Math.abs(latitude - 16.47) < 1e-10);
  assert.equal(longitude, 107.58);
  assert.equal(url.searchParams.get('travelmode'), 'driving');
});
