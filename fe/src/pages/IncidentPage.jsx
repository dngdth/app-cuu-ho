// src/pages/IncidentPage.jsx

import React, { useState, useMemo } from 'react';
import { Box } from '@mui/material';
import { AnimatePresence } from 'framer-motion';

import MapComponent from '../components/map/MapComponent';
import Sidebar from '../components/sidebar/Sidebar';
import SearchBar from '../components/search/SearchBar';
import FilterPanel from '../components/sidebar/filter/FilterPanel';
import IncidentCard from '../components/sidebar/incidents/IncidentCard';
import IncidentDetailView from '../components/sidebar/incidents/IncidentDetailView';
import { mockIncidents } from '../data/mockData'; 

export default function IncidentPage() {
  const [incidents] = useState(mockIncidents || []);
  const [selectedIncident, setSelectedIncident] = useState(null); 
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedRegion, setSelectedRegion] = useState('all');
  const [selectedTimeRange, setSelectedTimeRange] = useState('all');

  const filteredIncidents = useMemo(() => {
    return incidents.filter((incident) => {
      const matchesSearch = incident.title?.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesCategory = selectedCategory === 'all' || incident.categoryId === selectedCategory;
      const matchesRegion = selectedRegion === 'all' || incident.regionId === selectedRegion;
      return matchesSearch && matchesCategory && matchesRegion;
    });
  }, [incidents, searchTerm, selectedCategory, selectedRegion]);

  const handleMarkerClick = (incident) => {
    console.log("Marker clicked:", incident); // Debug log
    setSelectedIncident(incident);
  };

  const handleCardSelect = (incident) => {
    setSelectedIncident(incident);
  };

  return (
    <Box sx={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden', position: 'relative' }}>
      
      {/* --- A. SIDEBAR (TRÁI) --- */}
      <Box sx={{ 
          position: 'absolute', left: 0, top: 0, bottom: 0, zIndex: 10,
          // QUAN TRỌNG: Cho phép click xuyên qua vùng trống của container này
          pointerEvents: 'none' 
      }}>
        {/* Bọc Sidebar trong div này để bật lại click cho nội dung Sidebar */}
        <div style={{ pointerEvents: 'auto', height: '100%' }}>
            <Sidebar isOpen={true}>
                <SearchBar searchTerm={searchTerm} setSearchTerm={setSearchTerm} />
                <FilterPanel 
                    categories={[{id: 'flood', name: 'Lũ lụt'}, {id: 'fire', name: 'Cháy rừng'}]} 
                    regions={[{id: 'hcm', name: 'TP.HCM'}, {id: 'hn', name: 'Hà Nội'}]}
                    selectedCategory={selectedCategory} setSelectedCategory={setSelectedCategory}
                    selectedRegion={selectedRegion} setSelectedRegion={setSelectedRegion}
                    selectedTimeRange={selectedTimeRange} setSelectedTimeRange={setSelectedTimeRange}
                />
                <Box sx={{ px: '20px', pb: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    {filteredIncidents.map((incident) => (
                      <IncidentCard 
                        key={incident.id} 
                        incident={incident}
                        onSelect={() => handleCardSelect(incident)}
                        isSelected={selectedIncident?.id === incident.id}
                      />
                    ))}
                </Box>
            </Sidebar>
        </div>
      </Box>

      {/* --- B. MAP (NỀN) --- */}
      <Box sx={{ flex: 1, position: 'relative', zIndex: 1 }}>
        <MapComponent 
          incidents={filteredIncidents} 
          onMarkerClick={handleMarkerClick}
          selectedIncident={selectedIncident} 
        />
      </Box>

      {/* --- C. POPUP CHI TIẾT (MODAL) --- */}
      <AnimatePresence>
        {selectedIncident && (
          <IncidentDetailView 
            incident={selectedIncident} 
            onClose={() => setSelectedIncident(null)} 
          />
        )}
      </AnimatePresence>

    </Box>
  );
}
