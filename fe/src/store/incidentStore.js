// src/store/incidentStore.js
import { create } from 'zustand';
import { getAllRescueRequests } from '../services/rescueRequestService';
import { getAllRegions } from '../services/regionService';
import { getAllDisasterTypes } from '../services/disasterTypeService';
import { extractCoordsFromURL } from '../utils/mapUtils';
import { getUrgencyLevel } from '../utils/urgency';
import { getGeocodingStatus } from '../services/geocodeService';
import { getAllNeeds } from '../services/needsService';
import { getQualitySummary } from '../services/operationsService';
import { defaultFilters } from '../utils/incidentFilters';

// === Helper làm giàu dữ liệu ===
const enrichIncidents = (incidents, regions, categories) => {
  const regionMap = new Map(regions.map(reg => [reg.id, reg.name]));
  const categoryMap = new Map(categories.map(cat => [cat.id, cat.name]));

  return incidents.map(incident => {
    const coords = extractCoordsFromURL(incident.map_link);

    // GeoJSON format: [lng, lat]
    const coordinateLng = incident.coordinate?.coordinates?.[0];
    const coordinateLat = incident.coordinate?.coordinates?.[1];

    const locationLng = incident.location?.coordinates?.[0];
    const locationLat = incident.location?.coordinates?.[1];

    const rawLat =
      coordinateLat ??
      locationLat ??
      coords?.lat ??
      incident.latitude ??
      incident.lat ??
      null;

    const rawLng =
      coordinateLng ??
      locationLng ??
      coords?.lng ??
      incident.longitude ??
      incident.lng ??
      null;

    const latitude = rawLat != null && rawLat !== '' && Number.isFinite(Number(rawLat)) && Math.abs(Number(rawLat)) <= 90 ? Number(rawLat) : null;
    const longitude = rawLng != null && rawLng !== '' && Number.isFinite(Number(rawLng)) && Math.abs(Number(rawLng)) <= 180 ? Number(rawLng) : null;

    return {
      ...incident,
      regionName: regionMap.get(incident.region_id) || 'Không xác định',
      categoryName: incident.disaster_types?.map((type) => type.name).join(', ') || categoryMap.get(incident.category_id) || 'Khác',
      urgency: getUrgencyLevel(incident.urgency_score),
      latitude,
      longitude,
    };
  });
};

export const useIncidentStore = create((set, get) => ({
  // === STATE ===
  allIncidents: [],
  regions: [],
  categories: [],
  needs: [],
  qualitySummary: null,
  geocodingStatus: null,
  isLoading: true,
  isFetched: false,
  error: null,
  selectedIncident: null,
  filters: { ...defaultFilters },

  // === ACTIONS ===
  actions: {
    setFilters: (patch) => set((state) => ({ filters: { ...state.filters, ...patch } })),
    resetFilters: () => set({ filters: { ...defaultFilters } }),
    fetchInitialData: async (force = false) => {
      if (!force && (get().isFetched || get().isFetching)) return;
      set({ isLoading: !get().isFetched, isFetching: true, error: null });

      try {
        const [incidentsData, regionsData, categoriesData, geocodingStatus, needs, qualitySummary] = await Promise.all([
          getAllRescueRequests(),
          getAllRegions(),
          getAllDisasterTypes(),
          getGeocodingStatus().catch(() => null),
          getAllNeeds(),
          getQualitySummary(),
        ]);

        const enrichedData = enrichIncidents(incidentsData, regionsData, categoriesData);

        set({
          allIncidents: enrichedData,
          regions: regionsData,
          categories: categoriesData,
          geocodingStatus,
          needs,
          qualitySummary,
          selectedIncident: get().selectedIncident ? enrichedData.find((item) => item.id === get().selectedIncident.id) || null : null,
          isFetched: true,
        });
      } catch (error) {
        console.error('Failed to fetch initial data', error);
        set({ error: 'Không tải được dữ liệu cứu hộ. Kiểm tra kết nối backend.' });
      } finally {
        set({ isLoading: false, isFetching: false });
      }
    },

    setSelectedRegion: (regionId) => {
      set((state) => ({
        filters: { ...state.filters, selectedRegion: regionId },
      }));
    },

    setSelectedCategory: (categoryId) => {
      set((state) => ({
        filters: { ...state.filters, selectedCategory: categoryId },
      }));
    },

    setSelectedTimeRange: (timeRange) => {
      set((state) => ({
        filters: { ...state.filters, selectedTimeRange: timeRange },
      }));
    },

    setSearchTerm: (term) => {
      set((state) => ({
        filters: { ...state.filters, searchTerm: term },
      }));
    },

    setSelectedIncident: (incident) => {
      set({ selectedIncident: incident });
    },
  },
}));
