import React, { useState } from "react";
import PropTypes from "prop-types";
import {
  Card,
  CardContent,
  Typography,
  Chip,
  Box,
  IconButton,
} from '@mui/material';
import { motion } from 'framer-motion';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

// === Component Chính ===
const IncidentCard = ({ incident, onSelect, onExpand, isSelected }) => {
  const [isHovered, setIsHovered] = useState(false);

  const { title, description, status } = incident || {};
  const displayTitle = title || "Sự cố chưa có tiêu đề";
  const displayDesc = description || "Chưa có mô tả chi tiết về sự cố này.";
  const displayStatus = status || "Mới";

  return (
    <Card
      component={motion.div}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -3 }}
      transition={{ duration: 0.2 }}
      elevation={0}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onSelect}
      sx={{
        mb: 2,
        borderRadius: '16px',
        border: isSelected ? '2px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(0,0,0,0.08)',
        cursor: 'pointer',
        background: isSelected ? 'rgba(254, 242, 242, 0.6)' : '#FFFFFF',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        overflow: 'hidden',
        '&:hover': {
          boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
          borderColor: 'rgba(239, 68, 68, 0.3)',
        }
      }}
    >
      <Box sx={{ p: 2 }}>
        {/* Nội dung */}
        <CardContent sx={{ p: 0, '&:last-child': { pb: 0 }, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <Box>
            <Typography
              variant="h6"
              sx={{
                fontSize: '16px',
                fontWeight: 700,
                color: '#111827',
                mb: 0.8,
                lineHeight: 1.4,
                letterSpacing: '-0.01em',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {displayTitle}
            </Typography>

            <Typography
              variant="body2"
              sx={{
                fontSize: '13.5px',
                color: '#6B7280',
                lineHeight: 1.5,
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                overflow: 'hidden',
              }}
            >
              {displayDesc}
            </Typography>
          </Box>

          {/* Footer */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mt: 1.5 }}>
            <Chip
              label={displayStatus}
              size="small"
              sx={{
                height: 24,
                fontSize: '11.5px',
                fontWeight: 600,
                borderRadius: '8px',
                bgcolor: displayStatus === "Khẩn cấp" || displayStatus === "Cần cứu trợ"
                  ? '#FEF2F2'
                  : '#F0F9FF',
                color: displayStatus === "Khẩn cấp" || displayStatus === "Cần cứu trợ"
                  ? '#B91C1C'
                  : '#0369A1',
                border: `1px solid ${displayStatus === "Khẩn cấp" || displayStatus === "Cần cứu trợ"
                  ? '#FECACA'
                  : '#BAE6FD'}`,
              }}
            />

            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onExpand?.();
              }}
              sx={{
                width: 32,
                height: 32,
                borderRadius: '10px',
                border: isHovered ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid transparent',
                bgcolor: isHovered ? 'rgba(239, 68, 68, 0.08)' : 'rgba(243, 244, 246, 0.5)',
                color: isHovered ? '#DC2626' : '#6B7280',
                transition: 'all 0.2s ease',
                '&:hover': {
                  bgcolor: 'rgba(239, 68, 68, 0.12)',
                  color: '#DC2626',
                }
              }}
            >
              <ChevronRightIcon fontSize="small" />
            </IconButton>
          </Box>
        </CardContent>
      </Box>
    </Card>
  );
};

// === PropTypes ===
IncidentCard.propTypes = {
  incident: PropTypes.shape({
    title: PropTypes.string,
    description: PropTypes.string,
    status: PropTypes.string,
    image: PropTypes.string,
    imageUrl: PropTypes.string,
  }),
  onSelect: PropTypes.func,
  onExpand: PropTypes.func,
  isSelected: PropTypes.bool,
};

IncidentCard.defaultProps = {
  onSelect: () => {},
  onExpand: () => {},
  isSelected: false,
};

export default IncidentCard;
