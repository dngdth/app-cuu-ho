import { useEffect, useRef, useState } from 'react';
import { Alert, Box, Button, Stack, TextField, Typography } from '@mui/material';
import axiosClient from '../../api/axiosClient';
import { extractCoordsFromURL } from '../../utils/mapUtils';
import { directionsURL, nearestDestinations, routeColors } from '../../utils/nearbyRoutes';

const errorMessage = (error) => {
  const detail = error.response?.data?.detail;
  return typeof detail === 'string' ? detail : detail?.message || error.message || 'Chưa tìm được đường đi.';
};

export default function RoutePanel({ incidents, configured, canResolveLink, result, onRoute, onSelect }) {
  const [link, setLink] = useState(result?.sourceLink || '');
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const request = useRef(null);
  useEffect(() => () => request.current?.abort(), []);

  const clear = () => { request.current?.abort(); setError(''); onRoute(null); };
  const find = async (event) => {
    event.preventDefault();
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setError(''); setBusy(true); setProgress(0); onRoute(null);
    try {
      let coordinates = extractCoordsFromURL(link.trim());
      if (!coordinates) {
        if (!canResolveLink) throw new Error('Đăng nhập để đọc link rút gọn, hoặc dùng link Google Maps có ghim tọa độ.');
        const resolved = await axiosClient.post('/geocode/resolve-link', { url: link.trim() }, { timeout: 30000, signal: controller.signal });
        if (controller.signal.aborted) return;
        coordinates = { lng: resolved.coordinate.coordinates[0], lat: resolved.coordinate.coordinates[1] };
      }
      const origin = { latitude: coordinates.lat, longitude: coordinates.lng };
      let destinations = nearestDestinations(incidents, origin);
      if (!destinations.length) throw new Error('Chưa có địa điểm thiên tai có tọa độ để tìm đường.');
      const publish = () => {
        onRoute({ origin, sourceLink: link.trim(), destinations: [...destinations] });
      };
      publish();
      if (configured) {
        // Sequential requests share the backend's provider rate limit.
        for (let index = 0; index < destinations.length; index++) {
          setProgress(index + 1);
          const destination = destinations[index];
          try {
            const route = await axiosClient.post('/geocode/route', {
              start: { type: 'Point', coordinates: [origin.longitude, origin.latitude] },
              end: { type: 'Point', coordinates: [destination.longitude, destination.latitude] }, mode: 'drive',
            }, { timeout: 20000, signal: controller.signal });
            if (controller.signal.aborted) return;
            destinations = destinations.map((item, position) => position === index ? { ...item, route } : item);
          } catch (err) {
            if (controller.signal.aborted) return;
            destinations = destinations.map((item, position) => position === index ? { ...item, routeError: errorMessage(err) } : item);
          }
          publish();
        }
      }
    } catch (err) { if (!controller.signal.aborted) setError(errorMessage(err)); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  };

  return <Stack component="section" aria-label="Tìm đường tới các địa điểm thiên tai" spacing={1.5}
    sx={{ my: 2, p: 2, bgcolor: 'white', border: '1px solid #E5E7EB', borderRadius: 3 }}>
    <Typography fontWeight={700}>Tìm đường đến 5 địa điểm gần nhất</Typography>
    <Box component="form" onSubmit={find}>
      <TextField fullWidth required size="small" label="Link Google Maps vị trí hiện tại" value={link} disabled={busy}
        placeholder="https://maps.app.goo.gl/..."
        helperText="Chọn ghim vị trí của bạn trên Google Maps → Chia sẻ → Sao chép liên kết."
        onChange={(event) => { setLink(event.target.value); clear(); }} />
      <Stack direction="row" spacing={1} mt={1}>
        <Button type="submit" variant="contained" disabled={busy || !link.trim()}>
          {busy ? progress ? `Đang tìm đường ${progress}/${result?.destinations.length || 5}…` : 'Đang đọc vị trí…' : 'Tìm đường'}
        </Button>
        <Button disabled={busy || !result} onClick={clear}>Xóa đường</Button>
      </Stack>
    </Box>
    <Typography variant="caption" color="text.secondary">
      Chọn theo khoảng cách đường chim bay trong tất cả yêu cầu chưa kết thúc đã có tọa độ. Các yêu cầu cùng vị trí được tính là một địa điểm.
    </Typography>
    {result && <>
      <Typography variant="body2" fontWeight={600}>Đã tìm thấy {result.destinations.length} địa điểm gần bạn</Typography>
      {result.destinations.some((destination) => destination.routeError) && <Alert severity="info">
        {result.destinations.find((destination) => destination.routeError).routeError}
      </Alert>}
      <Stack component="ol" spacing={1.5} sx={{ m: 0, p: 0, listStyle: 'none' }}>
        {result.destinations.map((destination, index) => <Box component="li" key={destination.id}
          sx={{ borderLeft: `3px solid ${routeColors[index]}`, pl: 1.5 }}>
          <Typography variant="body2" fontWeight={700}>{index + 1}. {destination.title}</Typography>
          <Typography variant="caption" display="block" color="text.secondary">{destination.location || destination.regionName}</Typography>
          <Typography variant="caption" display="block">Cách bạn {destination.distance_km.toLocaleString('vi-VN', { maximumFractionDigits: 2 })} km đường chim bay</Typography>
          {destination.route && <Typography variant="body2">
            Đường đi: {(destination.route.distance_m / 1000).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} km · {Math.ceil(destination.route.duration_s / 60)} phút
          </Typography>}
          {destination.routeError && <Typography variant="caption" color="text.secondary" display="block">
            Chưa vẽ được tuyến đường. Bạn vẫn có thể mở chỉ đường trong Google Maps.
          </Typography>}
          <Stack direction="row" flexWrap="wrap">
            <Button size="small" onClick={() => onSelect(destination)}>Xem vị trí</Button>
            <Button size="small" component="a" href={directionsURL(result.origin, destination)} target="_blank" rel="noopener noreferrer">Chỉ đường Google Maps</Button>
          </Stack>
        </Box>)}
      </Stack>
      <Typography variant="caption" color="text.secondary">Đường đi tham khảo; chưa phản ánh ngập lụt hoặc đường đang bị chặn.</Typography>
    </>}
    {error && <Alert severity="error">{error}</Alert>}
  </Stack>;
}
