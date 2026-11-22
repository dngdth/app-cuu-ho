import { useEffect, useRef, useState } from 'react';
import { Alert, Box, CircularProgress, Typography } from '@mui/material';
import 'leaflet/dist/leaflet.css';
import CustomMarker from './CustomMarker';

const TILE_URL = import.meta.env.VITE_MAP_TILE_URL || 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const ATTRIBUTION = import.meta.env.VITE_MAP_ATTRIBUTION || '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>';

export default function MapComponent({ incidents, onMarkerClick, selectedIncident, route, focusKey = 'all' }) {
  const container = useRef(null);
  const fitted = useRef(null);
  const [context, setContext] = useState(null);
  const [error, setError] = useState('');
  const [tileError, setTileError] = useState(false);

  useEffect(() => {
    let cancelled = false, map, observer;
    import('leaflet').then((module) => {
      if (cancelled || !container.current) return;
      const L = module.default;
      map = L.map(container.current, { center: [16, 106.5], zoom: 5, zoomControl: false, preferCanvas: true });
      L.control.zoom({ position: 'topright' }).addTo(map);
      L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(map);
      L.tileLayer(TILE_URL, { attribution: ATTRIBUTION, maxZoom: 19, updateWhenIdle: true }).addTo(map)
        .on('tileerror', () => { if (!cancelled) setTileError(true); });
      observer = new ResizeObserver(() => map.invalidateSize({ pan: false }));
      observer.observe(container.current);
      setContext({ map, library: L });
    }).catch(() => { if (!cancelled) setError('Chưa tải được bản đồ. Hãy tải lại trang.'); });
    return () => { cancelled = true; observer?.disconnect(); map?.remove(); };
  }, []);

  useEffect(() => {
    if (!context || fitted.current === focusKey) return;
    const valid = incidents.filter((item) => Number.isFinite(item.latitude) && Number.isFinite(item.longitude));
    if (!valid.length) return;
    context.map.fitBounds(valid.map((item) => [item.latitude, item.longitude]), { padding: [50, 50], maxZoom: 14 });
    fitted.current = focusKey;
  }, [context, incidents, focusKey]);

  useEffect(() => {
    if (context && Number.isFinite(selectedIncident?.latitude) && Number.isFinite(selectedIncident?.longitude))
      context.map.setView([selectedIncident.latitude, selectedIncident.longitude], 16);
  }, [context, selectedIncident]);

  useEffect(() => {
    if (!context || !route?.geometry) return;
    const layer = context.library.geoJSON({ type: 'Feature', geometry: route.geometry, properties: {} },
      { style: { color: '#2563EB', weight: 5, opacity: 0.8 } }).addTo(context.map);
    context.map.fitBounds(layer.getBounds(), { padding: [50, 50] });
    return () => layer.remove();
  }, [context, route]);

  return <Box sx={{ height: '100%', width: '100%', position: 'relative', bgcolor: '#E8F0EB' }}>
    <Box ref={container} sx={{ height: '100%', width: '100%', zIndex: 0 }} role="region" aria-label="Bản đồ các yêu cầu cứu hộ" />
    {!context && !error && <Box sx={{ position: 'absolute', inset: 0, display: 'grid', placeContent: 'center', gap: 2 }}>
      <CircularProgress /><Typography>Đang tải bản đồ OpenStreetMap…</Typography>
    </Box>}
    {(error || tileError) && <Alert severity="warning" sx={{ position: 'absolute', top: 90, left: 20, right: 60, zIndex: 1 }}>
      {error || 'Chưa tải được một số ô nền bản đồ. Vị trí lưu sẵn và danh sách yêu cầu vẫn dùng được.'}
    </Alert>}
    {context && incidents.filter((item) => Number.isFinite(item.latitude) && Number.isFinite(item.longitude)).map((incident) =>
      <CustomMarker key={incident.id} incident={incident} context={context} onClick={onMarkerClick} isSelected={selectedIncident?.id === incident.id} />)}
  </Box>;
}
