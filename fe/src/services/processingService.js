import axiosClient from '../api/axiosClient';

export const processRecords = (records, options = {}) => axiosClient.post(
  '/processing/import', { records, ...options }, { timeout: 180000 },
);

export const readRescueCsv = async (file) => {
  const data = new FormData();
  data.append('file', file);
  return axiosClient.post('/processing/read-csv', data, {
    headers: { 'Content-Type': undefined },
  });
};
