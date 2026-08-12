import axiosInstance from './axiosInstance';

/** POST /api/auth/register/ */
export const register = (data) =>
  axiosInstance.post('/api/auth/register/', data);

/** POST /api/auth/verify-email/ */
export const verifyEmail = (data) =>
  axiosInstance.post('/api/auth/verify-email/', data);

/** POST /api/auth/resend-verification/ */
export const resendVerification = (data) =>
  axiosInstance.post('/api/auth/resend-verification/', data);

/** POST /api/auth/login/ */
export const login = (data) =>
  axiosInstance.post('/api/auth/login/', data);

/** POST /api/auth/google/ — exchange a Google ID token for app JWTs */
export const googleLogin = (credential) =>
  axiosInstance.post('/api/auth/google/', { credential });

/** POST /api/auth/token/refresh/ */
export const tokenRefresh = (data) =>
  axiosInstance.post('/api/auth/token/refresh/', data);

/** POST /api/auth/logout/ */
export const logout = (data) =>
  axiosInstance.post('/api/auth/logout/', data);

/** GET /api/auth/profile/ */
export const getProfile = () =>
  axiosInstance.get('/api/auth/profile/');

/** PATCH /api/auth/profile/ */
export const updateProfile = (data) =>
  axiosInstance.patch('/api/auth/profile/', data);

/** POST /api/auth/change-password/ */
export const changePassword = (data) =>
  axiosInstance.post('/api/auth/change-password/', data);

/** POST /api/auth/password-reset/ */
export const requestPasswordReset = (data) =>
  axiosInstance.post('/api/auth/password-reset/', data);

/** POST /api/auth/password-reset/confirm/ */
export const confirmPasswordReset = (data) =>
  axiosInstance.post('/api/auth/password-reset/confirm/', data);

/** GET /api/auth/users/ — admin only */
export const listUsers = () =>
  axiosInstance.get('/api/auth/users/');
