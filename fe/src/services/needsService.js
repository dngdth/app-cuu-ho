// src/services/needsService.js
import axiosClient from '../api/axiosClient';

/**
 * Needs Service
 * Handles all API calls related to rescue needs
 */

/**
 * Get all needs
 * @returns {Promise<Array>} List of needs
 */
export const getAllNeeds = async () => {
  const response = await axiosClient.get('/needs/');
  return response;
};

/**
 * Get a single need by ID
 * @param {number} needsId - Need ID
 * @returns {Promise<Object>} Need details
 */
export const getNeedsById = async (needsId) => {
  const response = await axiosClient.get(`/needs/${needsId}`);
  return response;
};

/**
 * Create a new need
 * @param {Object} data - Need data (name, description)
 * @returns {Promise<Object>} Created need
 */
export const createNeeds = async (data) => {
  const response = await axiosClient.post('/needs/', data);
  return response;
};

/**
 * Update an existing need
 * @param {number} needsId - Need ID
 * @param {Object} data - Updated need data
 * @returns {Promise<Object>} Updated need
 */
export const updateNeeds = async (needsId, data) => {
  const response = await axiosClient.put(`/needs/${needsId}`, data);
  return response;
};

/**
 * Delete a need
 * @param {number} needsId - Need ID
 * @returns {Promise<Object>} Deletion result
 */
export const deleteNeeds = async (needsId) => {
  const response = await axiosClient.delete(`/needs/${needsId}`);
  return response;
};
