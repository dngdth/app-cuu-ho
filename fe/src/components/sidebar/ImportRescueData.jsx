import { useState } from 'react';
import { Alert, Box, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle,
  FormControlLabel, Stack, Tab, Tabs, TextField, Typography } from '@mui/material';
import { readRescueCsv } from '../../services/processingService';
import { queueImport } from '../../services/jobService';
import axiosClient from '../../api/axiosClient';
import { canOperate, useAuthStore } from '../../store/authStore';

export default function ImportRescueData({ onQueued }) {
  const user = useAuthStore((s) => s.user);
  const [open, setOpen] = useState(false), [tab, setTab] = useState(0);
  const [file, setFile] = useState(null), [collectedAt, setCollectedAt] = useState('');
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [queuedId, setQueuedId] = useState('');
  const [raw, setRaw] = useState(''), [sourceUrl, setSourceUrl] = useState(''), [geocode, setGeocode] = useState(false);
  const [form, setForm] = useState({ content: '', location: '', map_link: '', contact: '', affected_people: '', needs: '', disaster_type: '',
    is_isolated: false, deathly: false, infrastructure_damage: false });
  const change = (e) => setForm((old) => ({ ...old, [e.target.name]: e.target.type === 'checkbox' ? e.target.checked : e.target.value }));
  const failure = (err) => setError(typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'Chưa xử lý được. Kiểm tra nội dung hoặc kết nối backend.');
  const extract = async () => {
    setBusy(true); setError('');
    try {
      const { record } = await axiosClient.post('/processing/extract', { content: raw, source_url: sourceUrl || null });
      setForm((old) => ({ ...old, ...record, affected_people: record.affected_people ?? '',
        location: record.location || '', contact: record.contact || '', map_link: record.map_link || '',
        needs: record.needs.join(', '), disaster_type: record.disaster_type.join(', ') }));
      setTab(1);
    } catch (err) { failure(err); }
    finally { setBusy(false); }
  };
  const submit = async () => {
    setBusy(true); setError(''); setQueuedId('');
    try {
      const records = tab === 0 ? (await readRescueCsv(file)).records : [{ ...form, source_url: sourceUrl || form.source_url || null }];
      const options = { geocode, ...(collectedAt ? { collected_at: new Date(collectedAt).toISOString() } : {}) };
      const job = await queueImport(records, options);
      setQueuedId(job.id); onQueued();
    } catch (err) { failure(err); }
    finally { setBusy(false); }
  };
  return <>
    <Box sx={{ px: 2.5, pb: 2 }}><Button fullWidth variant="contained" disabled={!canOperate(user)}
      onClick={() => { setOpen(true); setError(''); setQueuedId(''); }}>Nhập dữ liệu và đánh giá AI</Button></Box>
    <Dialog open={open} onClose={busy ? undefined : () => setOpen(false)} fullWidth maxWidth="sm">
      <DialogTitle>Thêm yêu cầu cứu hộ</DialogTitle><DialogContent>
        <Tabs value={tab} onChange={(_, value) => { if (!busy) { setTab(value); setQueuedId(''); } }} sx={{ mb: 2 }}>
          <Tab label="File CSV" /><Tab label="Thông tin yêu cầu" /><Tab label="Bóc tách bài viết" />
        </Tabs>
        {tab === 0 && <Stack spacing={2}>
          <Typography variant="body2">CSV UTF-8 có cột content. Tối đa 500 dòng, 3 MB. Danh sách yêu cầu sẽ tự cập nhật sau khi nhập xong.</Typography>
          <Button component="label" variant="outlined">{file?.name || 'Chọn file CSV'}<input hidden type="file" accept=".csv,text/csv" onChange={(e) => setFile(e.target.files[0] || null)} /></Button>
        </Stack>}
        {tab === 2 && <Stack spacing={2}><TextField multiline minRows={6} label="Dán nguyên bài viết nguồn" value={raw} onChange={(e) => setRaw(e.target.value)} />
          <TextField label="Link bài nguồn (nếu có)" value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} />
          <Alert severity="info">Bóc tách local không cần API. Chỉ lấy thông tin được ghi rõ; kết quả sẽ chuyển sang tab thông tin để bạn kiểm tra trước khi nhập.</Alert>
          <Button disabled={busy || !raw.trim()} onClick={extract}>Bóc tách và kiểm tra</Button></Stack>}
        {tab === 1 && <Stack spacing={2}>
          <TextField required multiline minRows={3} label="Nội dung cầu cứu" name="content" value={form.content} onChange={change} />
          {['location', 'map_link', 'contact', 'affected_people', 'disaster_type', 'needs'].map((name) => <TextField key={name}
            label={{ location: 'Địa chỉ', map_link: 'Link Google Maps nguồn', contact: 'Liên hệ', affected_people: 'Số người bị ảnh hưởng', disaster_type: 'Loại thiên tai (cách nhau bằng dấu phẩy)', needs: 'Nhu cầu (cách nhau bằng dấu phẩy)' }[name]}
            name={name} value={form[name]} onChange={change} type={name === 'affected_people' ? 'number' : 'text'} />)}
          <Box>{[['is_isolated', 'Bị cô lập'], ['deathly', 'Nguy hiểm tính mạng'], ['infrastructure_damage', 'Hư hại hạ tầng']].map(([key, label]) =>
            <FormControlLabel key={key} label={label} control={<Checkbox name={key} checked={!!form[key]} onChange={change} />} />)}</Box>
        </Stack>}
        {tab !== 2 && <Stack mt={2} spacing={2}>
          <TextField label="Thời điểm thu thập (nếu biết)" type="datetime-local" value={collectedAt} onChange={(e) => setCollectedAt(e.target.value)}
            slotProps={{ inputLabel: { shrink: true } }} helperText="Không biết thì để trống; không tự coi dữ liệu cũ là bài đăng hôm nay." />
          <FormControlLabel label="Tìm tọa độ khi nhập (dùng hạn mức Geoapify)" control={<Checkbox checked={geocode} onChange={(e) => setGeocode(e.target.checked)} />} />
          <Alert severity="info">Yêu cầu mới luôn chưa xác minh. AI hỗ trợ đánh giá, không thay thế kiểm tra thực tế.</Alert>
        </Stack>}
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        {queuedId && <Alert severity="success" sx={{ mt: 2 }}>Đã gửi yêu cầu nhập dữ liệu. Bạn có thể đóng hộp thoại; danh sách sẽ tự cập nhật sau khi xử lý xong.</Alert>}
      </DialogContent><DialogActions><Button disabled={busy} onClick={() => setOpen(false)}>Đóng</Button>
        {tab !== 2 && <Button variant="contained" onClick={submit} disabled={busy || !!queuedId || (tab === 0 ? !file : !form.content.trim())}>
          {busy ? 'Đang xếp hàng…' : 'Đánh giá và lưu'}</Button>}</DialogActions>
    </Dialog>
  </>;
}
