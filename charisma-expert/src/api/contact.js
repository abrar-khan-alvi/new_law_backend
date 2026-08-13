import axiosInstance from './axiosInstance';

export const sendContactMessage = (data) =>
  axiosInstance.post('/api/contact/', data);
