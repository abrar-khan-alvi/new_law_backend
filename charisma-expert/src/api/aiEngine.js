import axiosInstance from './axiosInstance';

/**
 * GET /api/ai/training-docs/
 * @param {{ doc_type?: string }} params
 */
export const listTrainingDocs = (params = {}) =>
  axiosInstance.get('/api/ai/training-docs/', { params });

/**
 * POST /api/ai/training-docs/upload/
 * Sends multipart/form-data: file, doc_type, title (optional)
 * @param {FormData} formData
 */
export const uploadTrainingDoc = (formData) =>
  axiosInstance.post('/api/ai/training-docs/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
