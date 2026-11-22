import assert from 'node:assert/strict';
import test from 'node:test';
import { filterIncidents } from '../src/utils/incidentFilters.js';
import { initialReview, reviewPatch } from '../src/utils/reviewForm.js';

const incident = { id: 1, title: 'Cần giúp', content: 'Gia đình đang chờ', location: '10/82 Đào Duy Anh, Huế',
  status: 'unverified', urgency_score: 3, region_id: 5, latitude: 16.46, longitude: 107.58,
  disaster_types: [{ id: 2, name: 'Lũ lụt' }], needs: [{ id: 3, name: 'Cứu hộ' }] };

test('accent-free address search combines urgency/status/region/category', () => {
  const filters = { searchTerm: 'dao duy anh', selectedStatus: 'unverified', selectedUrgency: 'high', selectedRegion: '5', selectedCategory: '2' };
  assert.deepEqual(filterIncidents([incident], filters), [incident]);
  assert.deepEqual(filterIncidents([incident], { ...filters, selectedStatus: 'resolved' }), []);
});
test('missing coordinates do not become zero; unknown and future dates do not pass recent filter', () => {
  const missing = { ...incident, latitude: null, longitude: null };
  assert.deepEqual(filterIncidents([incident, missing], { selectedLocation: 'missing' }), [missing]);
  const now = Date.parse('2026-11-21T00:00:00Z');
  assert.equal(filterIncidents([incident, { ...incident, posted_time: '2026-11-22' }], { selectedTimeRange: 'day' }, null, now).length, 0);
});
test('address edit omits old coordinates so backend can resolve the new address', () => {
  const initial = initialReview(incident);
  assert.deepEqual(reviewPatch(initial, { ...initial, location: 'Địa chỉ mới' }), { location: 'Địa chỉ mới' });
  assert.deepEqual(reviewPatch(initial, initial), {});
});
test('manual point uses GeoJSON longitude first and rejects incomplete/out-of-range pairs', () => {
  const initial = initialReview(incident);
  assert.deepEqual(reviewPatch(initial, { ...initial, latitude: '16.5', longitude: '107.6' }).coordinate, { type: 'Point', coordinates: [107.6, 16.5] });
  assert.throws(() => reviewPatch(initial, { ...initial, latitude: '' }));
  assert.throws(() => reviewPatch(initial, { ...initial, latitude: '91' }));
  assert.equal(reviewPatch(initial, { ...initial, latitude: '', longitude: '' }).coordinate, null);
});
