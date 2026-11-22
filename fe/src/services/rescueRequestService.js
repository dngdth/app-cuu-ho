// src/services/rescueRequestService.js
import axiosClient from '../api/axiosClient';

/**
 * Rescue Request Service
 * Handles all API calls related to rescue requests
 */

/**
 * Get all rescue requests with optional filtering
 * @param {Object} params - Query parameters (page, size, region_id, status, etc.)
 * @returns {Promise<Array>} List of rescue requests
 */
export const getAllRescueRequests = async (params = {}) => {
  if ('limit' in params || 'skip' in params) return axiosClient.get('/rescue_request/', { params });
  const records = [];
  const limit = 500;
  for (let skip = 0; ; skip += limit) {
    const page = await axiosClient.get('/rescue_request/', { params: { ...params, skip, limit } });
    if (!Array.isArray(page)) throw new Error('API rescue_request must return an array');
    records.push(...page);
    if (page.length < limit) return records;
  }
};

/**
 * Get a single rescue request by ID
 * @param {number} requestId - Rescue request ID
 * @returns {Promise<Object>} Rescue request details
 */
export const getRescueRequestById = async (requestId) => {
  const response = await axiosClient.get(`/rescue_request/${requestId}`);
  return response;
};

/**
 * Create a new rescue request
 * @param {Object} data - Rescue request data
 * @returns {Promise<Object>} Created rescue request
 */
export const createRescueRequest = async (data) => {
  const response = await axiosClient.post('/rescue_request/', data);
  return response;
};

/**
 * Update an existing rescue request
 * @param {number} requestId - Rescue request ID
 * @param {Object} data - Updated rescue request data
 * @returns {Promise<Object>} Updated rescue request
 */
export const updateRescueRequest = async (requestId, data) => {
  const response = await axiosClient.put(`/rescue_request/${requestId}`, data);
  return response;
};

/**
 * Delete a rescue request
 * @param {number} requestId - Rescue request ID
 * @returns {Promise<Object>} Deletion result
 */
export const deleteRescueRequest = async (requestId) => {
  const response = await axiosClient.delete(`/rescue_request/${requestId}`);
  return response;
};
