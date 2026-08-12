import axiosInstance from './axiosInstance';

/**
 * GET /api/blog/posts/
 * Supports query params: search, category, tag, page, etc.
 * Public endpoint — no auth required.
 * @param {{ search?: string, category?: string, page?: number }} params
 */
export const listPosts = (params = {}) =>
  axiosInstance.get('/api/blog/posts/', { params });

/**
 * GET /api/blog/posts/:slug/
 * Public endpoint. Increments view count.
 */
export const getPost = (slug) =>
  axiosInstance.get(`/api/blog/posts/${slug}/`);

/**
 * GET /api/blog/tags/
 * Public endpoint.
 */
export const listTags = () =>
  axiosInstance.get('/api/blog/tags/');

// --- Admin Endpoints ---

export const createPost = (data) =>
  axiosInstance.post('/api/blog/posts/', data);

export const updatePost = (slug, data) =>
  axiosInstance.patch(`/api/blog/posts/${slug}/`, data);

export const deletePost = (slug) =>
  axiosInstance.delete(`/api/blog/posts/${slug}/`);

export const addPostMedia = (slug, formData) => {
  // Axios automatically sets multipart/form-data with the correct boundary if formData is a FormData instance.
  // It also automatically sets application/json if formData is a plain object.
  return axiosInstance.post(`/api/blog/posts/${slug}/media/`, formData);
};

export const deletePostMedia = (slug, mediaId) =>
  axiosInstance.delete(`/api/blog/posts/${slug}/media/${mediaId}/`);
