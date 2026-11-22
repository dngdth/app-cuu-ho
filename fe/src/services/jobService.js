import axiosClient from '../api/axiosClient';

export const queueImport = (records, options = {}) => axiosClient.post('/jobs/import', { records, ...options });
export const queueGeocoding = (limit = 20, options = {}) => axiosClient.post('/jobs/geocode', { limit, ...options });
export const getJobs = () => axiosClient.get('/jobs');
export const jobAction = (id, action) => axiosClient.post(`/jobs/${id}/${action}`, {}, { timeout: 30000 });
