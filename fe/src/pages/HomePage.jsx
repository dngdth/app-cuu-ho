// src/pages/HomePage.jsx
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import MenuIcon from '@mui/icons-material/Menu';
import { Alert, Box, CircularProgress, Fab, Snackbar, Stack, Typography } from '@mui/material';
import { useCallback, useEffect, useState } from 'react';
import { useFilteredData } from '../hooks/useFilteredData';
import { useIncidentStore } from '../store/incidentStore';

// Import các component mới
import MapComponent from '../components/map/MapComponent';
import Sidebar from '../components/sidebar/SideBar';
import FilterPanel from '../components/sidebar/filter/FilterPanel';
import RescueCard from '../components/sidebar/incidents/RescueCard';
import SearchBar from '../components/sidebar/search/SearchBar';
import ImportRescueData from '../components/sidebar/ImportRescueData';
import LocatePending from '../components/sidebar/LocatePending';
import { urgencyStyles } from '../utils/urgency';
import { defaultFilters } from '../utils/incidentFilters';
import ReviewDialog from '../components/sidebar/incidents/ReviewDialog';
import AccountPanel from '../components/sidebar/AccountPanel';
import RoutePanel from '../components/map/RoutePanel';
import { canOperate, useAuthStore } from '../store/authStore';
import { getJobs } from '../services/jobService';

function HomePage() {
  // 1. Lấy state từ store với selector riêng lẻ để tránh tạo object mới mỗi render
  const allIncidents = useIncidentStore((state) => state.allIncidents);
  const filters = useIncidentStore((state) => state.filters);
  const selectedIncident = useIncidentStore((state) => state.selectedIncident);
  const isLoading = useIncidentStore((state) => state.isLoading);
  const error = useIncidentStore((state) => state.error);
  const geocodingStatus = useIncidentStore((state) => state.geocodingStatus);
  const categories = useIncidentStore((state) => state.categories);
  const regions = useIncidentStore((state) => state.regions);
  // Lấy actions từ store
  const fetchInitialData = useIncidentStore((state) => state.actions.fetchInitialData);
  const setSelectedIncident = useIncidentStore((state) => state.actions.setSelectedIncident);
  const setSearchTerm = useIncidentStore((state) => state.actions.setSearchTerm);
  const setFilters = useIncidentStore((state) => state.actions.setFilters);
  const resetFilters = useIncidentStore((state) => state.actions.resetFilters);
  const [reviewing, setReviewing] = useState(null);
  const [saved, setSaved] = useState(false);
  const [jobRefresh, setJobRefresh] = useState(0);
  const [route, setRoute] = useState(null);
  const user = useAuthStore((state) => state.user);
  const refreshData = useCallback(() => fetchInitialData(true), [fetchInitialData]);
  const queued = () => setJobRefresh((value) => value + 1);

  useEffect(() => {
    if (!canOperate(user)) return;
    let active = true, previous = '';
    const load = async () => {
      try {
        const jobs = await getJobs();
        if (!active) return;
        const snapshot = jobs.map((job) => `${job.id}:${job.progress}:${job.status}`).join(',');
        if (snapshot !== previous && (previous || jobs.some((job) => job.progress > 0))) refreshData();
        previous = snapshot;
      } catch { /* Retry on the next poll. */ }
    };
    load();
    const timer = setInterval(load, 3000);
    return () => { active = false; clearInterval(timer); };
  }, [user, jobRefresh, refreshData]);

  // 2. State riêng của HomePage
  const [mapBounds] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true); // State để điều khiển sidebar

  // 3. Sử dụng useEffect để fetch dữ liệu ban đầu
  useEffect(() => {
    fetchInitialData();
    const timer = setInterval(() => fetchInitialData(true), 60 * 60 * 1000);
    return () => clearInterval(timer);
  }, [fetchInitialData]);

  // 4. Sử dụng hook mới để lọc dữ liệu
  const filteredIncidents = useFilteredData(allIncidents, filters, mapBounds);

  // 5. Tối ưu hóa các hàm callback
  const handleFocusOnMap = useCallback((incident) => {
    setSelectedIncident(incident);
  }, [setSelectedIncident]);


  return (
    <Box sx={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif', bgcolor: '#F9FAFB' }}>
      {/* --- SIDEBAR --- */}
      <Sidebar isOpen={isSidebarOpen}>
        <AccountPanel />
        <SearchBar searchTerm={filters.searchTerm} setSearchTerm={setSearchTerm} />
        <RoutePanel incidents={allIncidents} configured={geocodingStatus?.configured && canOperate(user)}
          canResolveLink={canOperate(user)} result={route} onRoute={setRoute} onSelect={handleFocusOnMap} />
        <ImportRescueData onQueued={queued} />
        <LocatePending status={geocodingStatus}
          incidents={allIncidents} regions={regions}
          onView={(selectedRegion) => {
            setFilters({ ...defaultFilters, selectedRegion });
            setSelectedIncident(null);
          }}
          onLocated={queued} />
        {error && <Alert severity="error">{error}</Alert>}
        {!isLoading && <Typography variant="caption" sx={{ px: 2.5, pb: 1 }}>
          Hiển thị {filteredIncidents.length} / {allIncidents.length} yêu cầu · {filteredIncidents.filter((item) => item.latitude != null && item.longitude != null).length} có thể hiển thị trên bản đồ
        </Typography>}
        <FilterPanel
          categories={categories}
          regions={regions}
          filters={filters}
          setFilters={setFilters}
          onReset={resetFilters}
        />
        {isLoading && (
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              minHeight: '200px',
              flexDirection: 'column',
              gap: 2,
            }}
          >
            <CircularProgress
              size={50}
              thickness={4}
              sx={{ color: '#EF4444' }}
            />
            <Typography sx={{ color: '#6B7280', fontSize: '14px', fontWeight: 500 }}>
              Đang tải dữ liệu...
            </Typography>
          </Box>
        )}
        {!isLoading && (
          <Stack spacing={0}>
            {filteredIncidents.map((incident) => (
              <RescueCard
                key={incident.id}
                incident={incident}
                onFocus={handleFocusOnMap}
                onReview={canOperate(user) ? setReviewing : undefined}
              />
            ))}
          </Stack>
        )}
        {!isLoading && filteredIncidents.length === 0 && (
          <Box
            sx={{
              textAlign: 'center',
              p: 4,
              mt: 4,
              background: 'rgba(249, 250, 251, 0.8)',
              borderRadius: '16px',
              border: '1px solid rgba(0, 0, 0, 0.06)',
            }}
          >
            <Typography sx={{ color: '#6B7280', fontSize: '14px', mb: 1 }}>
              📭
            </Typography>
            <Typography sx={{ color: '#374151', fontSize: '14px', fontWeight: 500 }}>
              Không tìm thấy sự cố nào phù hợp
            </Typography>
          </Box>
        )}
      </Sidebar>

      <Box component="main" sx={{ flex: 1, position: 'relative' }}>
        <Box sx={{ position: 'absolute', bottom: 35, right: 12, zIndex: 5, bgcolor: 'white', p: 1.5, borderRadius: 2, boxShadow: 2 }}>
          <Typography variant="caption" fontWeight={700}>Mức khẩn cấp</Typography>
          {['high', 'medium', 'low'].map((key) => <Box key={key} sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
            <Box sx={{ width: urgencyStyles[key].size, height: urgencyStyles[key].size, borderRadius: '50%', bgcolor: urgencyStyles[key].color }} />
            <Typography variant="caption">{urgencyStyles[key].label}</Typography>
          </Box>)}
        </Box>
        <Fab
          aria-label={isSidebarOpen ? 'Thu gọn bảng điều khiển' : 'Mở bảng điều khiển'}
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          sx={{
            position: 'absolute',
            top: 20,
            left: 20,
            zIndex: 1000,
            backgroundColor: 'rgba(255, 255, 255, 0.98)',
            backdropFilter: 'blur(10px)',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            border: '1px solid rgba(0, 0, 0, 0.08)',
            '&:hover': {
              backgroundColor: 'white',
              transform: 'scale(1.05)',
              boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2)',
            },
            transition: 'all 0.2s ease',
          }}
        >
          {isSidebarOpen ? <ChevronLeftIcon /> : <MenuIcon />}
        </Fab>
        <MapComponent
            focusKey={filters.selectedRegion}
            incidents={filteredIncidents}
            onMarkerClick={(incident) => { handleFocusOnMap(incident); if (canOperate(user)) setReviewing(incident); }}
            selectedIncident={selectedIncident}
            route={route}
        />
      </Box>
      {reviewing && <ReviewDialog key={reviewing.id} incident={reviewing} onClose={() => setReviewing(null)}
        onSaved={async () => { await fetchInitialData(true); setReviewing(null); setSaved(true); }} />}
      <Snackbar open={saved} autoHideDuration={5000} onClose={() => setSaved(false)} message="Đã lưu thay đổi và ghi lịch sử kiểm tra." />
    </Box>
  );
}

export default HomePage;
