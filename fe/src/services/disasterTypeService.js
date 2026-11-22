// src/services/disasterTypeService.js
import axiosClient from '../api/axiosClient';

/**
 * Disaster Type Service
 * Handles all API calls related to disaster types
 */

/**
 * Get all disaster types
 * @returns {Promise<Array>} List of disaster types
 */
export const getAllDisasterTypes = async () => {
  const response = await axiosClient.get('/disaster-type/');
  return response;
};

/**
 * Get a single disaster type by ID
 * @param {number} disasterTypeId - Disaster type ID
 * @returns {Promise<Object>} Disaster type details
 */
export const getDisasterTypeById = async (disasterTypeId) => {
  const response = await axiosClient.get(`/disaster-type/${disasterTypeId}`);
  return response;
};

/**
 * Create a new disaster type
 * @param {Object} data - Disaster type data (name, description)
 * @returns {Promise<Object>} Created disaster type
 */
export const createDisasterType = async (data) => {
  const response = await axiosClient.post('/disaster-type/', data);
  return response;
};

/**
 * Update an existing disaster type
 * @param {number} disasterTypeId - Disaster type ID
 * @param {Object} data - Updated disaster type data
 * @returns {Promise<Object>} Updated disaster type
 */
export const updateDisasterType = async (disasterTypeId, data) => {
  const response = await axiosClient.put(`/disaster-type/${disasterTypeId}`, data);
  return response;
};

/**
 * Delete a disaster type
 * @param {number} disasterTypeId - Disaster type ID
 * @returns {Promise<Object>} Deletion result
 */
export const deleteDisasterType = async (disasterTypeId) => {
  const response = await axiosClient.delete(`/disaster-type/${disasterTypeId}`);
  return response;
};
