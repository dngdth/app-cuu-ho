import { useState } from 'react';
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import axiosClient from '../../api/axiosClient';
import { canOperate, useAuthStore } from '../../store/authStore';

const names = { baseline: 'Baseline đa số', gradient_boosting: 'Gradient Boosting', random_forest: 'Random Forest', lightgbm: 'LightGBM', ensemble: 'Kết hợp đã hiệu chỉnh' };

export default function ModelReport() {
  const user = useAuthStore((s) => s.user);
  const [open, setOpen] = useState(false), [report, setReport] = useState(null), [error, setError] = useState('');
  const load = async () => {
    setOpen(true); setError('');
    try { setReport(await axiosClient.get('/operations/model-report')); }
    catch { setError('Bộ model đang chạy chưa có báo cáo. Chạy script đánh giá rồi cấu hình RESCUE_MODEL_DIR.'); }
  };
  const download = async () => {
    try {
      const blob = await axiosClient.get('/operations/export', { responseType: 'blob' });
      const url = URL.createObjectURL(blob), anchor = document.createElement('a');
      anchor.href = url; anchor.download = 'rescue-requests.csv'; anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch { setError('Chưa xuất được dữ liệu. Cần đăng nhập với quyền vận hành.'); }
  };
  return <Box sx={{ mb: 2 }}><Stack direction="row"><Button onClick={load}>Đánh giá mô hình</Button>
    {canOperate(user) && <Button onClick={download}>Xuất CSV</Button>}</Stack>
    {error && !open && <Alert severity="error">{error}</Alert>}
    <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="md"><DialogTitle>Báo cáo đánh giá AI</DialogTitle>
      <DialogContent>{error && <Alert severity="warning">{error}</Alert>}
        {report && <Stack spacing={2}>
          <Alert severity="warning">Holdout nội bộ từ dữ liệu crawl, chưa phải kiểm chứng ngoài thực địa. Nhãn nguồn cần được kiểm toán; AI không xác minh tính thật/giả của bài đăng.</Alert>
          <Typography variant="body2">{report.rows} dòng · Train {report.split.train} · Calibration {report.split.calibration} · Test {report.split.test} · Nhóm trùng giữa tập phát triển và test: {report.split.group_intersection}</Typography>
          <Typography variant="caption" color="text.secondary">Báo cáo của bộ model hiện hành. Kết quả từng bài được lưu tại thời điểm xử lý; thay model không tự ghi đè các dự đoán đã lưu.</Typography>
          {Object.entries(report.targets).map(([target, results]) => <Box key={target}>
            <Typography fontWeight={700}>{target === 'urgency' ? 'Mức khẩn cấp' : 'Độ tin cậy theo nhãn nguồn'}</Typography>
            <Table size="small"><TableHead><TableRow><TableCell>Mô hình</TableCell><TableCell>Macro F1</TableCell><TableCell>Log loss (thấp hơn tốt hơn)</TableCell></TableRow></TableHead>
              <TableBody>{Object.entries(names).map(([key, name]) => <TableRow key={key}><TableCell>{name}</TableCell>
                <TableCell>{results[key]?.macro_f1.toFixed(3)}</TableCell><TableCell>{results[key]?.log_loss.toFixed(3)}</TableCell></TableRow>)}</TableBody></Table>
            <Box component="img" src={`${import.meta.env.VITE_API_URL || '/api'}/operations/model-figure/${target}`} alt={`Ma trận nhầm lẫn và đặc trưng ${target}`} sx={{ width: '100%', mt: 2 }} />
          </Box>)}
          {report.limitations.map((text) => <Typography key={text} variant="caption" color="text.secondary">{text}</Typography>)}
        </Stack>}
      </DialogContent><DialogActions><Button onClick={() => setOpen(false)}>Đóng</Button></DialogActions>
    </Dialog>
  </Box>;
}
