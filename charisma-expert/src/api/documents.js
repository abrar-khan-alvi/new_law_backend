import axiosInstance from './axiosInstance';

/**
 * POST /api/documents/generate/
 * @param {{ doc_type: string, narrative_style: string, form_data: object }} data
 */
export const generateDocument = (data) =>
  axiosInstance.post('/api/documents/generate/', data);

/**
 * GET /api/documents/
 * @param {{ page?: number, doc_type?: string, q?: string }} params
 */
export const listDocuments = (params = {}) =>
  axiosInstance.get('/api/documents/', { params });

/**
 * GET /api/documents/:pk/
 */
export const getDocument = (pk) =>
  axiosInstance.get(`/api/documents/${pk}/`);

/**
 * POST /api/documents/:pk/regenerate/
 */
export const regenerateDocument = (pk) =>
  axiosInstance.post(`/api/documents/${pk}/regenerate/`);

/**
 * POST /api/documents/:pk/export/
 * Returns binary data — caller must handle blob response.
 * @param {string} pk
 * @param {{ format: 'pdf'|'docx', edited_text?: string }} data
 */
export const exportDocument = (pk, data) =>
  axiosInstance.post(`/api/documents/${pk}/export/`, data, {
    responseType: 'blob',
  });

/**
 * POST /api/documents/:pk/supervisor-review/
 * @param {{ approved: boolean, notes?: string }} data
 */
export const supervisorReview = (pk, data) =>
  axiosInstance.post(`/api/documents/${pk}/supervisor-review/`, data);

/**
 * POST /api/documents/:pk/prosecutor-review/
 * Recorded by a supervisor/admin on the (external, login-less) prosecutor's behalf.
 * @param {{ reviewer_name: string, approved: boolean, notes?: string }} data
 */
export const prosecutorReview = (pk, data) =>
  axiosInstance.post(`/api/documents/${pk}/prosecutor-review/`, data);

/**
 * POST /api/documents/:pk/sign/
 * Built-in e-signature: typed full name + server timestamp + IP.
 * @param {{ full_name: string }} data
 */
export const signDocument = (pk, data) =>
  axiosInstance.post(`/api/documents/${pk}/sign/`, data);
