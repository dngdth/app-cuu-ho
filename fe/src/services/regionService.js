// src/services/regionService.js
import axiosClient from '../api/axiosClient';

/**
 * Region Service
 * Handles all API calls related to regions
 */

/**
 * Get all regions
 * @returns {Promise<Array>} List of regions
 */
export const getAllRegions = async () => {
  const response = await axiosClient.get('/region/');
  return response;
};

/**
 * Get a single region by ID
 * @param {number} regionId - Region ID
 * @returns {Promise<Object>} Region details
 */
export const getRegionById = async (regionId) => {
  const response = await axiosClient.get(`/region/${regionId}`);
  return response;
};

/**
 * Create a new region
 * @param {Object} data - Region data (name, parent_id)
 * @returns {Promise<Object>} Created region
 */
export const createRegion = async (data) => {
  const response = await axiosClient.post('/region/', data);
  return response;
};

/**
 * Update an existing region
 * @param {number} regionId - Region ID
 * @param {Object} data - Updated region data
 * @returns {Promise<Object>} Updated region
 */
export const updateRegion = async (regionId, data) => {
  const response = await axiosClient.put(`/region/${regionId}`, data);
  return response;
};

/**
 * Delete a region
 * @param {number} regionId - Region ID
 * @returns {Promise<Object>} Deletion result
 */
export const deleteRegion = async (regionId) => {
  const response = await axiosClient.delete(`/region/${regionId}`);
  return response;
};

/**
 * Import regions from CSV file
 * @param {File} file - CSV file to import
 * @returns {Promise<Object>} Import result
 */
export const importRegionsFromCSV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axiosClient.post('/region/import-csv', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response;
};
