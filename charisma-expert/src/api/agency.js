import axiosInstance from './axiosInstance';

// ── Jurisdiction Profiles ────────────────────────────────────────────────────
// Shared state/federal defaults (citations, formatting) that agencies inherit
// from. Adding a new state or federal district means creating one of these,
// not writing new code.

/** GET /api/admin-panel/jurisdiction-profiles/ */
export const listJurisdictionProfiles = () =>
  axiosInstance.get('/api/admin-panel/jurisdiction-profiles/');

/** POST /api/admin-panel/jurisdiction-profiles/ */
export const createJurisdictionProfile = (data) =>
  axiosInstance.post('/api/admin-panel/jurisdiction-profiles/', data);

/** PATCH /api/admin-panel/jurisdiction-profiles/:pk/ */
export const updateJurisdictionProfile = (pk, data) =>
  axiosInstance.patch(`/api/admin-panel/jurisdiction-profiles/${pk}/`, data);

/** DELETE /api/admin-panel/jurisdiction-profiles/:pk/ */
export const deleteJurisdictionProfile = (pk) =>
  axiosInstance.delete(`/api/admin-panel/jurisdiction-profiles/${pk}/`);

// ── Agencies ─────────────────────────────────────────────────────────────────
// Court caption, judge title, prosecuting authority, and citations become
// printed legal text on warrants — admin-only, not self-service.

/** GET /api/admin-panel/agencies/ (paginated) */
export const listAgencies = (params = {}) =>
  axiosInstance.get('/api/admin-panel/agencies/', { params });

/** POST /api/admin-panel/agencies/ */
export const createAgency = (data) =>
  axiosInstance.post('/api/admin-panel/agencies/', data);

/** GET /api/admin-panel/agencies/:pk/ */
export const getAgency = (pk) =>
  axiosInstance.get(`/api/admin-panel/agencies/${pk}/`);

/** PATCH /api/admin-panel/agencies/:pk/ */
export const updateAgency = (pk, data) =>
  axiosInstance.patch(`/api/admin-panel/agencies/${pk}/`, data);

/** DELETE /api/admin-panel/agencies/:pk/ */
export const deleteAgency = (pk) =>
  axiosInstance.delete(`/api/admin-panel/agencies/${pk}/`);

/**
 * POST /api/admin-panel/agencies/:pk/seal/ — multipart upload.
 * @param {string|number} pk
 * @param {FormData} formData - must contain a "seal" file field.
 */
export const uploadAgencySeal = (pk, formData) =>
  axiosInstance.post(`/api/admin-panel/agencies/${pk}/seal/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
