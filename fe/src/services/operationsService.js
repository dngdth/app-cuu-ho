import axiosClient from '../api/axiosClient';

export const getQualitySummary = () => axiosClient.get('/operations/summary');
export const getRequestEvents = (id) => axiosClient.get(`/operations/requests/${id}/events`);
export const reviewRequest = (id, data) => axiosClient.patch(`/operations/requests/${id}/review`, data, { timeout: 60000 });
