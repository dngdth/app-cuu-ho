// src/components/sidebar/incidents/IncidentDetailView.jsx
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CloseIcon from '@mui/icons-material/Close';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import NavigationIcon from '@mui/icons-material/Navigation';
import PeopleIcon from '@mui/icons-material/People';
import {
    Box,
    Button,
    Card,
    Chip,
    Dialog,
    DialogActions,
    DialogContent,
    Divider,
    IconButton,
    Stack,
    Typography,
} from '@mui/material';
import { motion } from 'framer-motion';

// Cấu hình màu (Giữ nguyên)
const urgencyConfig = {
  critical: { label: 'KHẨN CẤP', color: '#DC2626', bg: '#FEF2F2' },
  high: { label: 'CAO', color: '#D97706', bg: '#FFFBEB' },
  medium: { label: 'TRUNG BÌNH', color: '#2563EB', bg: '#EFF6FF' },
  low: { label: 'THẤP', color: '#059669', bg: '#ECFDF5' },
};

const getUrgencyLevel = (score) => {
  if (score >= 8) return 'critical';
  if (score >= 6) return 'high';
  if (score >= 4) return 'medium';
  return 'low';
};

export default function IncidentDetailView({ incident, onClose }) {
  if (!incident) return null;

  const urgencyLevel = getUrgencyLevel(incident.urgency_score || 0);
  const urgencyStyle = urgencyConfig[urgencyLevel];

  return (
    <Dialog
      open={!!incident}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        component: motion.div,
        initial: { scale: 0.9, opacity: 0 },
        animate: { scale: 1, opacity: 1 },
        exit: { scale: 0.9, opacity: 0 },
        transition: { type: 'spring', damping: 25, stiffness: 300 },
        sx: {
          borderRadius: '24px',
          overflow: 'hidden',
          maxHeight: '90vh',
        }
      }}
      sx={{
        '& .MuiBackdrop-root': {
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          backdropFilter: 'blur(4px)',
        }
      }}
    >
      {/* Close Button */}
      <IconButton
        onClick={onClose}
        sx={{
          position: 'absolute',
          top: 12,
          right: 12,
          zIndex: 10,
          bgcolor: 'rgba(255,255,255,0.9)',
          backdropFilter: 'blur(4px)',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          '&:hover': {
            bgcolor: 'white',
            transform: 'scale(1.1)',
          }
        }}
      >
        <CloseIcon />
      </IconButton>

      <DialogContent sx={{ p: 3, pt: 4, bgcolor: '#FFFFFF' }}>
        {/* Header Badges & Title */}
        <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
          <Chip
            label={urgencyStyle.label}
            size="small"
            sx={{
              bgcolor: urgencyStyle.bg,
              color: urgencyStyle.color,
              fontWeight: 700,
              fontSize: '11px',
              height: '26px',
              px: 1,
            }}
          />
          <Chip
            label={incident.categoryName || 'Sự cố'}
            size="small"
            sx={{
              bgcolor: '#F3F4F6',
              color: '#374151',
              fontWeight: 600,
              fontSize: '11px',
              height: '26px',
              px: 1,
            }}
          />
        </Stack>

        <Typography
          variant="h5"
          fontWeight={800}
          sx={{
            color: '#111827',
            mb: 2,
            lineHeight: 1.3,
            fontSize: '22px',
          }}
        >
          {incident.title}
        </Typography>

        {/* Meta Info */}
        <Stack spacing={1.5} sx={{ mb: 2.5 }}>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', color: '#6B7280' }}>
            <LocationOnIcon fontSize="small" sx={{ color: '#EF4444' }} />
            <Typography variant="body2" fontWeight={500} sx={{ color: '#374151' }}>
              {incident.regionName}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', color: '#6B7280' }}>
            <AccessTimeIcon fontSize="small" />
            <Typography variant="body2">
              {incident.posted_time ? new Date(incident.posted_time).toLocaleString('vi-VN') : 'N/A'}
            </Typography>
          </Box>
          {incident.affected_people && (
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', color: '#D97706' }}>
              <PeopleIcon fontSize="small" />
              <Typography variant="body2" fontWeight={600}>
                {incident.affected_people.toLocaleString()} người bị ảnh hưởng
              </Typography>
            </Box>
          )}
        </Stack>

        <Divider sx={{ my: 2.5 }} />

        {/* Description */}
        <Typography
          variant="body1"
          sx={{
            color: '#374151',
            lineHeight: 1.7,
            fontSize: '15px',
            mb: 3,
          }}
        >
          {incident.content}
        </Typography>

        {/* Stats Grid */}
        {(incident.affected_people || incident.urgency_score) && (
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            {incident.affected_people && (
              <Card elevation={0} sx={{ p: 2.5, bgcolor: '#F9FAFB', borderRadius: '12px', textAlign: 'center', border: '1px solid rgba(0,0,0,0.05)' }}>
                <Typography variant="caption" sx={{ color: '#6B7280', display: 'block', mb: 0.5, fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Ảnh hưởng
                </Typography>
                <Typography variant="h6" fontWeight={700} color="#111827" sx={{ fontSize: '20px' }}>
                  {incident.affected_people.toLocaleString()}
                </Typography>
              </Card>
            )}
            {incident.urgency_score && (
              <Card elevation={0} sx={{ p: 2.5, bgcolor: '#F9FAFB', borderRadius: '12px', textAlign: 'center', border: '1px solid rgba(0,0,0,0.05)' }}>
                <Typography variant="caption" sx={{ color: '#6B7280', display: 'block', mb: 0.5, fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Mức độ
                </Typography>
                <Typography variant="h6" fontWeight={700} sx={{ color: urgencyStyle.color, fontSize: '20px' }}>
                  {incident.urgency_score}/10
                </Typography>
              </Card>
            )}
          </Box>
        )}
      </DialogContent>

      {/* Footer Actions */}
      <DialogActions sx={{ p: 2.5, pt: 0, bgcolor: '#FFFFFF' }}>
        <Button
          variant="contained"
          fullWidth
          size="large"
          startIcon={<NavigationIcon />}
          sx={{
            borderRadius: '12px',
            bgcolor: '#2563EB',
            fontWeight: 700,
            py: 1.5,
            fontSize: '14px',
            textTransform: 'none',
            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.25)',
            '&:hover': {
              bgcolor: '#1D4ED8',
              boxShadow: '0 6px 16px rgba(37, 99, 235, 0.35)',
            }
          }}
        >
          Chỉ đường tới đây
        </Button>
      </DialogActions>
    </Dialog>
  );
}
