import { useEffect, useState } from 'react';
import { Alert, Box, Button, Checkbox, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle,
  Divider, FormControlLabel, MenuItem, Stack, Tab, Tabs, TextField, Typography } from '@mui/material';
import { getRequestEvents, reviewRequest } from '../../../services/operationsService';
import { useIncidentStore } from '../../../store/incidentStore';
import { statusLabels } from '../../../utils/incidentFilters';
import { flagLabels, initialReview, reviewPatch } from '../../../utils/reviewForm';
import { useAuthStore } from '../../../store/authStore';

const changeLabels = { title: 'Tiêu đề', location: 'Địa chỉ', contact: 'Liên hệ', region_id: 'Mã khu vực',
  affected_people: 'Số người', status: 'Trạng thái', needs_ids: 'Mã nhu cầu', disaster_type_ids: 'Mã thiên tai',
  coordinate: 'Tọa độ', ai: 'Dự đoán AI', ...flagLabels };
const displayValue = (value) => value == null ? 'Chưa có' : typeof value === 'boolean' ? (value ? 'Có' : 'Không')
  : Array.isArray(value) ? value.join(', ') || 'Chưa có' : statusLabels[value] || String(value);

export default function ReviewDialog({ incident, onClose, onSaved }) {
  const [initial] = useState(() => initialReview(incident));
  const [form, setForm] = useState(initial);
  const [tab, setTab] = useState(0);
  const [note, setNote] = useState('');
  const user = useAuthStore((state) => state.user);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [events, setEvents] = useState(null);
  const [historyError, setHistoryError] = useState('');
  const geocoding = incident.prediction?.geocoding;
  const suggestions = Date.parse(geocoding?.expires_at) > Date.now() ? geocoding?.suggestions || [] : [];
  const regions = useIncidentStore((s) => s.regions);
  const categories = useIncidentStore((s) => s.categories);
  const needs = useIncidentStore((s) => s.needs);
  const update = (name, value) => setForm((state) => ({ ...state, [name]: value }));
  useEffect(() => {
    let active = true;
    getRequestEvents(incident.id).then((rows) => { if (active) setEvents(rows); })
      .catch(() => { if (active) setHistoryError('Không tải được lịch sử. Đóng và mở lại để thử lại.'); });
    return () => { active = false; };
  }, [incident.id]);

  const save = async () => {
    setError('');
    try {
      const patch = reviewPatch(initial, form);
      if (!Object.keys(patch).length) throw new Error('Chưa có thông tin nào thay đổi.');
      if (note.trim().length < 3) throw new Error('Ghi rõ căn cứ kiểm tra hoặc lý do thay đổi.');
      setSaving(true);
      await reviewRequest(incident.id, { ...patch, note: note.trim() });
      await onSaved();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail.map((r) => `${r.loc.at(-1)}: ${r.msg}`).join('; ') : detail || err.message);
    } finally { setSaving(false); }
  };

  return <Dialog open onClose={saving ? undefined : onClose} fullWidth maxWidth="md">
    <DialogTitle>Kiểm tra yêu cầu #{incident.id}</DialogTitle>
    <Tabs value={tab} onChange={(_, value) => setTab(value)} variant="fullWidth">
      <Tab label="Thông tin và xử lý" /><Tab label="Lịch sử thay đổi" />
    </Tabs>
    <DialogContent dividers>
      {tab === 0 ? <Stack spacing={2.5}>
        <Alert severity="info">Điểm AI chỉ hỗ trợ đánh giá. Chuyển sang “Chờ xử lý” sau khi đã kiểm tra yêu cầu và ghi căn cứ xác minh.</Alert>
        <Box><Typography variant="subtitle2">Nội dung nguồn</Typography>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', maxHeight: 180, overflow: 'auto', bgcolor: '#F9FAFB', p: 2 }}>{incident.content || 'Chưa có nội dung'}</Typography></Box>
        <TextField label="Tiêu đề" value={form.title} onChange={(e) => update('title', e.target.value)} required />
        <TextField label="Địa chỉ cụ thể" multiline minRows={2} value={form.location} onChange={(e) => update('location', e.target.value)}
          helperText="Khi đổi địa chỉ, tọa độ cũ được xóa và hệ thống tìm lại bằng Geoapify nếu đã có key. Có thể nhập tọa độ đã kiểm tra bên dưới." />
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2 }}>
          <TextField select label="Khu vực" value={form.region_id} onChange={(e) => update('region_id', e.target.value)}>
            <MenuItem value="">Chưa xác định</MenuItem>{regions.map((r) => <MenuItem key={r.id} value={r.id}>{r.name}</MenuItem>)}
          </TextField>
          <TextField label="Liên hệ" value={form.contact} onChange={(e) => update('contact', e.target.value)} />
          <TextField label="Số người bị ảnh hưởng" type="number" value={form.affected_people} onChange={(e) => update('affected_people', e.target.value)} slotProps={{ htmlInput: { min: 0, max: 1000000 } }} />
          <TextField select label="Trạng thái" value={form.status} onChange={(e) => update('status', e.target.value)}>
            {[initial.status, ...(incident.allowed_next_statuses || [])].map((key) => <MenuItem key={key} value={key}>{statusLabels[key] || key}</MenuItem>)}
          </TextField>
        </Box>
        {[['needs_ids', 'Nhu cầu', needs], ['disaster_type_ids', 'Loại thiên tai', categories]].map(([key, label, options]) =>
          <TextField key={key} select label={label} value={form[key]} onChange={(e) => update(key, e.target.value)}
            slotProps={{ select: { multiple: true, renderValue: (ids) => ids.map((id) => options.find((r) => r.id === id)?.name || id).join(', ') } }}>
            {options.map((r) => <MenuItem key={r.id} value={r.id}><Checkbox checked={form[key].includes(r.id)} />{r.name}</MenuItem>)}
          </TextField>)}
        <Box sx={{ display: 'flex', flexWrap: 'wrap' }}>{Object.entries(flagLabels).map(([key, label]) =>
          <FormControlLabel key={key} control={<Checkbox checked={form[key]} onChange={(e) => update(key, e.target.checked)} />} label={label} />)}</Box>
        <Divider />
        <Typography variant="subtitle2">Vị trí đã kiểm tra</Typography>
        {suggestions.length > 0 && <Alert severity="warning">
          Đã tìm thấy tuyến đường đúng khu vực. Các điểm dưới đây chỉ đại diện tuyến đường, chưa phải vị trí số nhà cần cứu hộ.
          Mở bản đồ đối chiếu, rồi nhập tọa độ nhà đã xác nhận vào các ô bên dưới.
        </Alert>}
        {suggestions.map((suggestion, index) => <Box key={suggestion.place_id || index} sx={{ p: 1.5, border: '1px solid #F59E0B', borderRadius: 2 }}>
          <Typography variant="body2">{suggestion.formatted_address} · Gợi ý tuyến đường</Typography>
          <Button component="a" target="_blank" rel="noopener noreferrer"
            href={`https://maps.google.com/?q=${suggestion.coordinate.coordinates[1]},${suggestion.coordinate.coordinates[0]}`}>
            Mở vị trí gợi ý trên bản đồ
          </Button>
          <Typography variant="caption" display="block">© Geoapify, © OpenStreetMap contributors</Typography>
        </Box>)}
        <TextField label="Link Google Maps nguồn" value={form.map_link} onChange={(e) => update('map_link', e.target.value)} />
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField fullWidth label="Vĩ độ (latitude)" value={form.latitude} onChange={(e) => update('latitude', e.target.value)} />
          <TextField fullWidth label="Kinh độ (longitude)" value={form.longitude} onChange={(e) => update('longitude', e.target.value)} />
          <Button onClick={() => setForm((state) => ({ ...state, latitude: '', longitude: '' }))}>Xóa tọa độ</Button>
        </Stack>
        <Typography variant="caption" color="text.secondary">Nhập theo vị trí bạn đã đối chiếu. Tọa độ thủ công không cần API key.</Typography>
        <Divider />
        <TextField label="Người ghi nhận" value={user ? `${user.name} (${user.email})` : ''} slotProps={{ input: { readOnly: true } }} />
        <TextField required multiline minRows={2} label="Căn cứ kiểm tra / lý do thay đổi" value={note} onChange={(e) => setNote(e.target.value)} slotProps={{ htmlInput: { maxLength: 2000 } }} />
        {error && <Alert severity="error">{error}</Alert>}
      </Stack> : <Stack spacing={2}>
        {historyError && <Alert severity="error">{historyError}</Alert>}
        {!events && !historyError && <CircularProgress size={24} />}
        {events?.length === 0 && <Typography color="text.secondary">Chưa có lịch sử kiểm tra. Bản ghi nhập trước khi có chức năng này không có lịch sử hồi tố.</Typography>}
        {events?.map((event) => <Box key={event.id} sx={{ p: 2, border: '1px solid #E5E7EB', borderRadius: 2 }}>
          <Typography fontWeight={700}>{event.actor} · {new Date(event.created_at).toLocaleString('vi-VN')}</Typography>
          <Typography sx={{ whiteSpace: 'pre-wrap', mb: 1 }}>{event.note}</Typography>
          {Object.entries(event.changes).map(([key, change]) => <Typography key={key} variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
            {changeLabels[key] || key}: {key === 'ai' ? 'Đã tính lại bằng 3 mô hình' : `${displayValue(change.before)} → ${displayValue(change.after)}${change.source ? ` (${change.source})` : ''}`}
          </Typography>)}
        </Box>)}
        <Typography variant="caption" color="text.secondary">Hiển thị tối đa 200 thay đổi mới nhất. Thay đổi mới ghi danh tính từ tài khoản đăng nhập; bản ghi lịch sử cũ có thể dùng tên tự nhập.</Typography>
      </Stack>}
    </DialogContent>
    <DialogActions><Button disabled={saving} onClick={onClose}>Đóng</Button>
      {tab === 0 && <Button variant="contained" disabled={saving} onClick={save}>{saving ? 'Đang lưu...' : 'Lưu thay đổi'}</Button>}
    </DialogActions>
  </Dialog>;
}
