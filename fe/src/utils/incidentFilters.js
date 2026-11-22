import { getUrgencyLevel } from './urgency.js';

export const statusLabels = {
  unverified: 'Chưa xác minh', pending: 'Đã xác minh · Chờ xử lý',
  in_progress: 'Đang xử lý', resolved: 'Đã giải quyết', rejected: 'Đã loại bỏ',
};
export const defaultFilters = {
  searchTerm: '', selectedCategory: 'all', selectedRegion: 'all', selectedTimeRange: 'all',
  selectedStatus: 'all', selectedUrgency: 'all', selectedLocation: 'all',
};
export const fold = (text) => String(text ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase();
export const hasCoordinates = (item) => Number.isFinite(item.latitude) && Number.isFinite(item.longitude);

export function filterIncidents(items, filters, bounds = null, now = Date.now()) {
  const f = { ...defaultFilters, ...filters };
  const search = fold(f.searchTerm).trim();
  return items.filter((item) => {
    if (search && !fold([item.title, item.content, item.location, item.contact, item.regionName].join(' ')).includes(search)) return false;
    if (f.selectedCategory !== 'all' && !item.disaster_types?.some((r) => r.id === Number(f.selectedCategory))) return false;
    if (f.selectedRegion !== 'all' && item.region_id !== Number(f.selectedRegion)) return false;
    if (f.selectedStatus !== 'all' && (item.status || 'unverified') !== f.selectedStatus) return false;
    if (f.selectedUrgency !== 'all' && getUrgencyLevel(item.urgency_score) !== f.selectedUrgency) return false;
    if (f.selectedLocation === 'located' && !hasCoordinates(item)) return false;
    if (f.selectedLocation === 'missing' && hasCoordinates(item)) return false;
    if (f.selectedTimeRange !== 'all') {
      const date = Date.parse(item.posted_time);
      const days = { day: 1, week: 7, month: 30 }[f.selectedTimeRange] || 1;
      if (!Number.isFinite(date) || date > now || date < now - days * 86400000) return false;
    }
    return !bounds || (hasCoordinates(item) && bounds.contains([item.longitude, item.latitude]));
  });
}
