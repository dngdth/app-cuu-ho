import { Box, Button, MenuItem, Stack, TextField, Typography } from '@mui/material';
import { statusLabels } from '../../../utils/incidentFilters';
import { urgencyStyles } from '../../../utils/urgency';

export default function FilterPanel({ categories, regions, filters, setFilters, onReset }) {
  const choices = [
    ['selectedStatus', 'Trạng thái', Object.entries(statusLabels)],
    ['selectedUrgency', 'Mức khẩn cấp', Object.entries(urgencyStyles).map(([key, value]) => [key, value.label])],
    ['selectedLocation', 'Vị trí trên bản đồ', [['located', 'Đã có tọa độ'], ['missing', 'Chưa có tọa độ']]],
    ['selectedRegion', 'Khu vực', regions.map((r) => [r.id, r.name])],
    ['selectedCategory', 'Loại thiên tai', categories.map((r) => [r.id, r.name])],
    ['selectedTimeRange', 'Thời gian đăng', [['day', '24 giờ qua'], ['week', '7 ngày qua'], ['month', '30 ngày qua']]],
  ];
  return <Box sx={{ p: 2, my: 2, border: '1px solid #E5E7EB', borderRadius: 3, bgcolor: 'white' }}>
    <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
      <Typography fontWeight={700}>Bộ lọc yêu cầu</Typography><Button size="small" onClick={onReset}>Đặt lại</Button>
    </Stack>
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))' }, gap: 2 }}>
      {choices.map(([name, label, options]) => <TextField key={name} select size="small" label={label}
        value={filters[name]} onChange={(event) => setFilters({ [name]: event.target.value })}>
        <MenuItem value="all">Tất cả</MenuItem>
        {options.map(([value, text]) => <MenuItem key={value} value={String(value)}>{text}</MenuItem>)}
      </TextField>)}
    </Box>
    <Typography variant="caption" color="text.secondary" display="block" mt={1}>Lọc thời gian chỉ áp dụng khi đã biết ngày đăng gốc.</Typography>
  </Box>;
}
