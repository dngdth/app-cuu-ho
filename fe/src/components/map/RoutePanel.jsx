import { useState } from 'react';
import { Alert, Button, Stack, TextField, Typography } from '@mui/material';
import axiosClient from '../../api/axiosClient';

export default function RoutePanel({ incident, configured, onRoute }) {
  const [lat, setLat] = useState('');
  const [lng, setLng] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  if (!incident || incident.latitude == null || incident.longitude == null) return null;
  const find = async () => {
    setError(''); setBusy(true);
    try {
      if (lat.trim() === '' || lng.trim() === '' || !Number.isFinite(Number(lat)) || !Number.isFinite(Number(lng)) || Math.abs(Number(lat)) > 90 || Math.abs(Number(lng)) > 180)
        throw new Error('Nhập đủ vĩ độ và kinh độ điểm xuất phát.');
      const route = await axiosClient.post('/geocode/route', {
        start: { type: 'Point', coordinates: [Number(lng), Number(lat)] },
        end: { type: 'Point', coordinates: [incident.longitude, incident.latitude] }, mode: 'drive',
      }, { timeout: 20000 });
      setResult(route); onRoute(route);
    } catch (err) { setError(typeof err.response?.data?.detail === 'string' ? err.response.data.detail : err.message); }
    finally { setBusy(false); }
  };
  return <Stack spacing={1.5} sx={{ my: 2, p: 2, bgcolor: 'white', border: '1px solid #E5E7EB', borderRadius: 3 }}>
    <Typography fontWeight={700}>Đường đi đến yêu cầu #{incident.id}</Typography>
    {!configured && <Alert severity="info">Cần Geoapify key và đăng nhập để tìm đường. Vị trí trên bản đồ vẫn xem được.</Alert>}
    <Stack direction="row" spacing={1}><TextField size="small" label="Vĩ độ xuất phát" value={lat} onChange={(e) => setLat(e.target.value)} />
      <TextField size="small" label="Kinh độ xuất phát" value={lng} onChange={(e) => setLng(e.target.value)} /></Stack>
    <Stack direction="row" spacing={1}><Button disabled={busy || !configured} onClick={find}>{busy ? 'Đang tìm…' : 'Tìm đường'}</Button>
      <Button onClick={() => { onRoute(null); setResult(null); }}>Xóa đường</Button></Stack>
    {result && <Typography variant="body2">{((result.distance_m || 0) / 1000).toFixed(1)} km · {Math.ceil((result.duration_s || 0) / 60)} phút (ước tính)</Typography>}
    {result && <Alert severity="warning">{result.warning}</Alert>}
    {error && <Alert severity="error">{error}</Alert>}
  </Stack>;
}
