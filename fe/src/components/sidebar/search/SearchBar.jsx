import SearchIcon from '@mui/icons-material/Search';
import { Box, InputAdornment, TextField } from '@mui/material';

export default function SearchBar({ searchTerm, setSearchTerm }) {
  return (
    <Box sx={{ mb: 2.5 }}>
      <TextField
        fullWidth
        placeholder="Tìm kiếm địa điểm, khu vực..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        variant="outlined"
        size="medium"
        sx={{
          '& .MuiOutlinedInput-root': {
            borderRadius: '14px',
            backgroundColor: '#FFFFFF',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            boxShadow: '0 1px 3px rgba(0,0,0,0.08)',

            '& fieldset': {
              border: '1px solid rgba(0,0,0,0.08)',
              transition: 'all 0.3s ease',
            },

            '&:hover': {
              backgroundColor: '#FFFFFF',
              boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
              '& fieldset': {
                borderColor: 'rgba(239, 68, 68, 0.2)',
              },
            },

            '&.Mui-focused': {
              backgroundColor: '#FFFFFF',
              boxShadow: '0 4px 16px rgba(239, 68, 68, 0.12)',
              '& fieldset': {
                borderColor: '#EF4444',
                borderWidth: '2px',
              },
              '& .MuiSvgIcon-root': {
                color: '#EF4444',
              }
            },
          },

          '& .MuiInputBase-input': {
            color: '#111827',
            fontWeight: 500,
            fontSize: '15px',
            padding: '12px 14px',
            '&::placeholder': {
              color: '#9CA3AF',
              opacity: 1,
              fontWeight: 400,
            },
          },
        }}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start" sx={{ ml: 0.5 }}>
              <SearchIcon
                sx={{
                  color: '#9CA3AF',
                  fontSize: 22,
                  transition: 'color 0.3s ease'
                }}
              />
            </InputAdornment>
          ),
        }}
      />
    </Box>
  );
}
