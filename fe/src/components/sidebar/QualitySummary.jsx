import { Box, Button, Stack, Typography } from '@mui/material';

export default function QualitySummary({ summary, onFilter }) {
  if (!summary) return null;
  const metrics = [
    ['Tổng yêu cầu', summary.total, {}],
    ['Chưa xác minh', summary.statuses.unverified || 0, { selectedStatus: 'unverified' }],
    ['Khẩn cấp cao', summary.urgencies.high || 0, { selectedUrgency: 'high' }],
    ['Chưa có tọa độ', summary.missing_coordinates, { selectedLocation: 'missing' }],
  ];
  return <Box sx={{ my: 2, p: 2, borderRadius: 3, bgcolor: '#FFF7ED' }}>
    <Typography fontWeight={700} mb={1}>Tổng quan dữ liệu</Typography>
    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
      {metrics.map(([label, count, filter]) => <Button key={label} onClick={() => onFilter(filter)} sx={{ textTransform: 'none', bgcolor: 'white', justifyContent: 'flex-start' }}>
        <Stack alignItems="flex-start"><Typography fontWeight={800} fontSize={24}>{count}</Typography><Typography variant="caption">{label}</Typography></Stack>
      </Button>)}
    </Box>
    <Typography variant="caption" display="block" mt={1} color="text.secondary">
      {summary.located} đã định vị · {summary.missing_address} thiếu địa chỉ · {summary.missing_region} chưa rõ khu vực
    </Typography>
    <Typography variant="caption" color="text.secondary">{summary.missing_posted_time} chưa rõ ngày đăng · {summary.missing_prediction} chưa có kết quả mô hình. Dữ liệu nguồn cần được xác minh trước khi điều phối.</Typography>
  </Box>;
}
