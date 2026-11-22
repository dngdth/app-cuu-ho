import CircleIcon from '@mui/icons-material/Circle';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import { Box, Chip, Paper, Typography } from '@mui/material';
import { AnimatePresence, motion } from 'framer-motion';
import { useIncidentStore } from '../../store/incidentStore';

// === 1. Cấu hình Animation ===
const sidebarVariants = {
  open: {
    width: 420,
    x: 0,
    opacity: 1,
    transition: {
      type: 'spring',
      stiffness: 400,
      damping: 30,
      mass: 0.8,
    },
  },
  closed: {
    width: 0,
    x: -50,
    opacity: 0,
    transition: {
      type: 'spring',
      stiffness: 400,
      damping: 30,
      mass: 0.8,
    },
  },
};

// Định nghĩa bộ font chuẩn, ưu tiên font đẹp -> font hệ thống Windows (Segoe UI)
const FONT_STACK = '"Be Vietnam Pro", "Inter", "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif';

export default function Sidebar({ isOpen, children }) {
  const error = useIncidentStore((state) => state.error);
  const loading = useIncidentStore((state) => state.isLoading);
  return (
    <AnimatePresence>
      {isOpen && (
        <Box
          component={motion.div}
          variants={sidebarVariants}
          initial="closed"
          animate="open"
          exit="closed"
          sx={{
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            height: '100dvh',
            width: 420,
            maxWidth: { xs: 'calc(100vw - 80px)', sm: 420 },
            flexShrink: 0,
            background: 'linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(249,250,251,0.95) 100%)',
            backdropFilter: 'blur(24px) saturate(180%)',
            WebkitBackdropFilter: 'blur(24px) saturate(180%)',
            borderRight: '1px solid rgba(0,0,0,0.06)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
            position: 'relative',
            zIndex: 100,
          }}
        >
          {/* === Header === */}
          <Paper
            elevation={0}
            sx={{
              p: 3,
              background: 'linear-gradient(135deg, #EF4444 0%, #DC2626 100%)',
              borderRadius: 0,
              borderBottom: '1px solid rgba(255,255,255,0.1)',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box
                component={motion.div}
                whileHover={{ scale: 1.08, rotate: 5 }}
                transition={{ type: "spring", stiffness: 400, damping: 10 }}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: 56,
                  height: 56,
                  borderRadius: '16px',
                  background: 'rgba(255,255,255,0.2)',
                  backdropFilter: 'blur(10px)',
                  boxShadow: '0 8px 16px rgba(0,0,0,0.15)',
                  border: '1px solid rgba(255,255,255,0.3)',
                }}
              >
                <LocalHospitalIcon sx={{ fontSize: 32, color: '#FFFFFF' }} />
              </Box>

              <Box sx={{ flex: 1 }}>
                <Typography
                  sx={{
                    fontFamily: FONT_STACK, // SỬA: Dùng bộ font đã tối ưu
                    fontWeight: 800,
                    fontSize: '20px',
                    color: '#FFFFFF',
                    letterSpacing: '-0.02em',
                    lineHeight: 1.2,
                    textShadow: '0 2px 4px rgba(0,0,0,0.1)',
                  }}
                >
                  CỨU HỘ KHẨN CẤP
                </Typography>
                <Typography
                  sx={{
                    fontFamily: FONT_STACK, // SỬA: Dùng bộ font đã tối ưu
                    fontSize: '13px',
                    color: 'rgba(255,255,255,0.9)',
                    fontWeight: 500,
                    mt: 0.5,
                  }}
                >
                  Hệ thống điều phối & ứng cứu
                </Typography>
              </Box>
            </Box>
          </Paper>

          {/* === Status Bar === */}
          <Box
            sx={{
              px: 3,
              py: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: '1px solid rgba(0,0,0,0.05)',
              backgroundColor: 'rgba(255,255,255,0.8)',
            }}
          >
            <Typography
              variant="caption"
              sx={{
                fontFamily: FONT_STACK, // SỬA: Thêm font cho text nhỏ
                color: '#6B7280',
                fontWeight: 600,
                fontSize: '11px',
                letterSpacing: '0.5px',
                textTransform: 'uppercase',
              }}
            >
              Trạng thái hệ thống
            </Typography>
            <Chip
              icon={<CircleIcon sx={{ fontSize: 8, color: '#10B981' }} />}
              label={error ? 'Mất kết nối' : loading ? 'Đang tải' : 'Trực tuyến'}
              size="small"
              sx={{
                height: 24,
                bgcolor: '#ECFDF5',
                color: '#059669',
                border: '1px solid #A7F3D0',
                fontSize: '11px',
                fontWeight: 700,
                fontFamily: FONT_STACK, // SỬA: Thêm font cho chip
                '& .MuiChip-icon': {
                  ml: 1,
                  animation: 'pulse 2s ease-in-out infinite',
                },
                '@keyframes pulse': {
                  '0%, 100%': { opacity: 1 },
                  '50%': { opacity: 0.5 },
                },
              }}
            />
          </Box>

          {/* === Content === */}
          <Box
            sx={{
              flex: 1,
              overflowY: 'auto',
              p: 2.5,
              fontFamily: FONT_STACK, // SỬA: Áp dụng cho nội dung bên trong
              '&::-webkit-scrollbar': {
                width: '6px',
              },
              '&::-webkit-scrollbar-track': {
                background: 'transparent',
              },
              '&::-webkit-scrollbar-thumb': {
                background: 'rgba(0,0,0,0.12)',
                borderRadius: '10px',
                '&:hover': {
                  background: 'rgba(0,0,0,0.18)',
                },
              },
            }}
          >
            {children}
          </Box>

          {/* === Footer Blur Gradient === */}
          <Box
            sx={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: '60px',
              background: 'linear-gradient(to top, rgba(249,250,251,0.95) 0%, transparent 100%)',
              pointerEvents: 'none',
              zIndex: 10,
            }}
          />
        </Box>
      )}
    </AnimatePresence>
  );
}
