export const flagLabels = {
  infrastructure_damage: 'Hư hỏng hạ tầng', is_isolated: 'Bị cô lập', deathly: 'Nguy hiểm tính mạng',
  has_emergency: 'Có dấu hiệu khẩn cấp', has_emotion: 'Có cảm xúc mạnh', has_emphasis: 'Có nhấn mạnh',
};

export function initialReview(incident) {
  return {
    title: incident.title || '', location: incident.location || '', contact: incident.contact || '',
    map_link: incident.prediction?.source_map_link || '', region_id: incident.region_id || '',
    affected_people: incident.affected_people ?? '', status: incident.status || 'unverified',
    needs_ids: (incident.needs || []).map((r) => r.id).sort((a, b) => a - b),
    disaster_type_ids: (incident.disaster_types || []).map((r) => r.id).sort((a, b) => a - b),
    latitude: incident.latitude ?? '', longitude: incident.longitude ?? '',
    ...Object.fromEntries(Object.keys(flagLabels).map((key) => [key, !!incident[key]])),
  };
}

export function reviewPatch(initial, current) {
  const patch = {};
  for (const key of Object.keys(initial)) {
    if (['latitude', 'longitude'].includes(key)) continue;
    let value = current[key];
    if (Array.isArray(value)) value = [...value].sort((a, b) => a - b);
    if (JSON.stringify(value) === JSON.stringify(initial[key])) continue;
    if (['region_id', 'affected_people'].includes(key)) value = value === '' ? null : Number(value);
    if (['location', 'contact', 'map_link'].includes(key)) value = value.trim() || null;
    patch[key] = value;
  }
  if (current.latitude !== initial.latitude || current.longitude !== initial.longitude) {
    if (current.latitude === '' && current.longitude === '') patch.coordinate = null;
    else {
      const lat = Number(current.latitude), lng = Number(current.longitude);
      if (current.latitude === '' || current.longitude === '' || !Number.isFinite(lat) || !Number.isFinite(lng) || Math.abs(lat) > 90 || Math.abs(lng) > 180)
        throw new Error('Nhập đủ vĩ độ (-90 đến 90) và kinh độ (-180 đến 180), hoặc xóa cả hai.');
      patch.coordinate = { type: 'Point', coordinates: [lng, lat] };
    }
  }
  return patch;
}
