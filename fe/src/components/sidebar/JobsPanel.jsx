import { useEffect, useState } from 'react';
import { Alert, Box, Button, LinearProgress, Stack, Typography } from '@mui/material';
import { getJobs, jobAction } from '../../services/jobService';
import axiosClient from '../../api/axiosClient';
import { canOperate, useAuthStore } from '../../store/authStore';

const labels = { queued: 'Đang chờ', running: 'Đang xử lý', completed: 'Hoàn tất', failed: 'Lỗi', blocked: 'Cần kiểm tra cấu hình/hạn mức', cancelled: 'Đã hủy' };

export default function JobsPanel({ refreshKey, onChanged }) {
  const user = useAuthStore((s) => s.user);
  const [jobs, setJobs] = useState([]), [usage, setUsage] = useState(null), [error, setError] = useState('');
  useEffect(() => {
    if (!canOperate(user)) return;
    let active = true;
    let previous = '';
    const load = async () => {
      try {
        const [rows, budget] = await Promise.all([getJobs(), axiosClient.get('/geocode/usage')]);
        if (!active) return;
        setJobs(rows); setUsage(budget);
        const snapshot = rows.map((r) => `${r.id}:${r.progress}:${r.status}`).join(',');
        if (snapshot !== previous && (previous || rows.some((row) => row.progress > 0 || row.status === 'completed'))) onChanged();
        previous = snapshot;
      } catch { if (active) setError('Chưa tải được tiến độ tác vụ.'); }
    };
    load();
    const timer = setInterval(load, 3000);
    return () => { active = false; clearInterval(timer); };
  }, [user, refreshKey, onChanged]);
  if (!canOperate(user)) return null;
  const act = async (id, action) => {
    try { await jobAction(id, action); setJobs(await getJobs()); onChanged(); }
    catch { setError('Chưa thực hiện được thao tác. Hãy thử tải lại trang.'); }
  };
  return <Box sx={{ my: 2, p: 2, border: '1px solid #E5E7EB', borderRadius: 3 }}>
    <Typography fontWeight={700}>Tác vụ nền và hạn mức API</Typography>
    {usage && Object.entries(usage.services).map(([name, item]) => <Typography key={name} variant="caption" display="block">
      {name === 'geocoding' ? 'Định vị' : 'Tìm đường'}: {item.day_used}/{item.day_limit} hôm nay · {item.month_used}/{item.month_limit} tháng này (UTC)
    </Typography>)}
    {error && <Alert severity="error">{error}</Alert>}
    {!jobs.length && <Typography variant="caption" color="text.secondary">Chưa có tác vụ. Nhập CSV hoặc định vị để bắt đầu.</Typography>}
    {jobs.slice(0, 6).map((job) => <Stack spacing={0.5} key={job.id} sx={{ mt: 2 }}>
      <Typography variant="body2">{job.kind === 'import' ? 'Nhập dữ liệu' : 'Định vị'} · {labels[job.status]} · {job.progress}/{job.total}</Typography>
      <LinearProgress variant="determinate" value={job.total ? job.progress / job.total * 100 : 100} />
      <Typography variant="caption">{job.kind === 'geocode'
        ? `Đã có tọa độ ${job.report.located || 0} · Gợi ý tuyến đường ${job.report.suggested || 0} · Chưa tìm được ${Math.max(0, (job.report.unlocated || 0) - (job.report.suggested || 0))}`
        : `Thêm ${job.report.created || 0} · Trùng ${job.report.duplicates || 0} · Định vị ${job.report.located || 0} · Lỗi ${job.report.failed || 0}`}</Typography>
      {job.error && <Typography variant="caption" color="error">{job.error}</Typography>}
      {(job.report.results || []).filter((row) => row.error).slice(0, 3).map((row) => <Typography key={row.row} variant="caption" color="error">Dòng {row.row}: {row.error}</Typography>)}
      <Stack direction="row">{['queued', 'running', 'blocked'].includes(job.status) && <Button size="small" onClick={() => act(job.id, 'cancel')}>Hủy tác vụ</Button>}
        {['failed', 'blocked'].includes(job.status) && <Button size="small" onClick={() => act(job.id, 'retry')}>Thử lại</Button>}</Stack>
    </Stack>)}
  </Box>;
}
