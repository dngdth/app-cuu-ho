import { useState } from 'react';
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { queueGeocoding } from '../../services/jobService';
import { canOperate, useAuthStore } from '../../store/authStore';
import { fold, hasCoordinates } from '../../utils/incidentFilters';

export default function LocatePending({ status, incidents, regions, onLocated, onView }) {
  const user = useAuthStore((s) => s.user);
  const [regionId, setRegionId] = useState(null);
  const [busy, setBusy] = useState(false), [message, setMessage] = useState(''), [error, setError] = useState('');
  const selectedRegion = regionId ?? String(regions.find((region) => ['hue', 'thua thien hue'].includes(fold(region.name)))?.id ?? 'all');
  const regionName = regions.find((region) => String(region.id) === selectedRegion)?.name;
  const scope = regionName ? `tại ${regionName}` : 'trong tất cả khu vực';
  const scoped = incidents.filter((item) => selectedRegion === 'all' || item.region_id === Number(selectedRegion));
  const pendingCount = scoped.filter((item) => !hasCoordinates(item)).length;
  const batchCount = Math.min(20, pendingCount);
  const locate = async () => {
    setBusy(true); setMessage(''); setError('');
    try {
      const job = await queueGeocoding(20, selectedRegion === 'all' ? {} : { region_id: Number(selectedRegion) });
      setMessage(`Đang định vị ${job.total} yêu cầu ${scope}. Danh sách và bản đồ sẽ tự cập nhật khi có kết quả.`);
      onView(selectedRegion);
      onLocated();
    }
    catch (err) { setError(typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'Chưa tạo được tác vụ định vị.'); }
    finally { setBusy(false); }
  };
  return <Box sx={{ px: 2.5, pb: 2 }}>
    {status && !status.configured && <Alert severity="info" sx={{ mb: 1 }}>{status.message}</Alert>}
    <Stack spacing={1.5}>
      <TextField select fullWidth size="small" label="Khu vực cần định vị" value={selectedRegion} disabled={busy}
        onChange={(event) => { setRegionId(event.target.value); setMessage(''); setError(''); }}>
        <MenuItem value="all">Tất cả khu vực</MenuItem>
        {regions.filter((region) => region.parent_id == null).map((region) =>
          <MenuItem key={region.id} value={String(region.id)}>{region.name}</MenuItem>)}
      </TextField>
      <Typography variant="body2" color="text.secondary">
        {scoped.length} yêu cầu {scope} · {scoped.length - pendingCount} đã có tọa độ · {pendingCount} chưa có tọa độ
      </Typography>
      <Button variant="outlined" fullWidth disabled={busy || !batchCount || !status?.configured || !canOperate(user)} onClick={locate}>
        {busy ? 'Đang xếp hàng…' : batchCount ? `Định vị ${batchCount} yêu cầu ${scope}` : 'Không còn yêu cầu chưa có tọa độ'}
      </Button>
      <Button fullWidth disabled={!scoped.length || busy} onClick={() => onView(selectedRegion)}>
        Xem {scoped.length} yêu cầu {scope}
      </Button>
      <Typography variant="caption" color="text.secondary">Mỗi lượt tối đa 20 yêu cầu, ưu tiên địa chỉ chưa từng tra cứu. Kết quả không khớp vẫn cần kiểm tra thủ công.</Typography>
    </Stack>
    {message && <Alert severity="success" sx={{ mt: 1 }}>{message}</Alert>}
    {error && <Alert severity="error" sx={{ mt: 1 }}>{error}</Alert>}
  </Box>;
}
