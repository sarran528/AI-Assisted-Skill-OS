import axios, { AxiosInstance } from 'axios';
import { useAuthStore } from '../store/authStore';

const baseURL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/?$/, '/');
console.log('[DEBUG] Axios Base URL:', baseURL);

const axiosClient: AxiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: add auth token
axiosClient.interceptors.request.use(
  (config) => {
    // Get the latest token from store state
    const authState = useAuthStore.getState();
    const token = authState.token;
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401
axiosClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().clearAuth();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default axiosClient;
