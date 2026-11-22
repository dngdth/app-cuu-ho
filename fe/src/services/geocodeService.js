import axiosClient from '../api/axiosClient';

export const getGeocodingStatus = () => axiosClient.get('/geocode/status');
export const locatePendingRequests = (options = {}) => axiosClient.post(
  '/processing/geocode-pending', { limit: 20, ...options }, { timeout: 180000 },
);
