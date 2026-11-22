// src/services/rescueService.js
import axiosClient from '../api/axiosClient';
import { mockIncidents, mockRegions } from '../data/mockData';

// Toggle this to switch between mock data and real API
const USE_MOCK_DATA = false;

// Helper to handle various response structures
// Note: axiosClient interceptor already unwraps response.data,
// so 'res' here is the actual data, not the axios response object
const handleResponse = (res) => {
  if (!res) return res;

  // If already an array, return as-is
  if (Array.isArray(res)) return res;

  // Check for nested data structures
  if (res?.data !== undefined) {
    if (Array.isArray(res.data)) return res.data;
    if (res.data?.items !== undefined) return res.data.items;
    if (res.data?.results !== undefined) return res.data.results;
  }

  // Top-level items/results
  if (Array.isArray(res?.items)) return res.items;
  if (Array.isArray(res?.results)) return res.results;

  // Other common array keys
  if (Array.isArray(res?.list)) return res.list;
  if (Array.isArray(res?.rows)) return res.rows;
  if (Array.isArray(res?.content)) return res.content;

  // Return as-is if no array found
  return res;
};

// --- RESCUE REQUEST ---
export const getRescueRequests = async (params = {}) => {
  if (USE_MOCK_DATA) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    return mockIncidents;
  }

  // GET /rescue_request
  // ví dụ params: { page: 1, size: 20, region_id: 3, status: 'open' }
  const res = await axiosClient.get('/rescue_request/', { params });
  return handleResponse(res);
};

export const getRescueRequestById = async (id) => {
  if (USE_MOCK_DATA) {
    await new Promise(resolve => setTimeout(resolve, 300));
    return mockIncidents.find(incident => incident.id === id);
  }

  // GET /rescue_request/{id}
  const res = await axiosClient.get(`/rescue_request/${id}/`);
  return handleResponse(res);
};

export const createRescueRequest = async (payload) => {
  if (USE_MOCK_DATA) {
    await new Promise(resolve => setTimeout(resolve, 500));
    console.log('Mock create:', payload);
    return { ...payload, id: Date.now() };
  }

  // POST /rescue_request
  const res = await axiosClient.post('/rescue_request/', payload);
  return handleResponse(res);
};

export const updateRescueRequest = async (id, payload) => {
  if (USE_MOCK_DATA) {
    await new Promise(resolve => setTimeout(resolve, 500));
    console.log('Mock update:', id, payload);
    return { ...payload, id };
  }

  // PUT/PATCH /rescue_request/{id} (tùy BE)
  const res = await axiosClient.put(`/rescue_request/${id}/`, payload);
  return handleResponse(res);
};

export const deleteRescueRequest = async (id) => {
  if (USE_MOCK_DATA) {
    await new Promise(resolve => setTimeout(resolve, 500));
    console.log('Mock delete:', id);
    return { success: true };
  }

  // DELETE /rescue_request/{id}
  const res = await axiosClient.delete(`/rescue_request/${id}/`);
  return handleResponse(res);
};

// --- CATEGORY / REGION / SOURCE ---

export const getRegions = async (params = {}) => {
  if (USE_MOCK_DATA) {
    await new Promise(resolve => setTimeout(resolve, 300));
    return mockRegions;
  }

  // GET /region
  const res = await axiosClient.get('/region/', { params });
  return handleResponse(res);
};
