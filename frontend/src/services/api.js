import axios from 'axios';

const baseURL =
  import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '/api' : 'http://localhost:8000/api');

const api = axios.create({
  baseURL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  const role = localStorage.getItem('userRole');
  const userId = localStorage.getItem('userId');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (role) {
    config.headers['X-Role'] = role;
  }
  if (userId) {
    config.headers['X-User-Id'] = userId;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      localStorage.getItem('refreshToken')
    ) {
      originalRequest._retry = true;
      try {
        const { data } = await axios.post(`${baseURL}/auth/refresh`, {
          refresh_token: localStorage.getItem('refreshToken'),
        });
        if (data.access_token) {
          localStorage.setItem('accessToken', data.access_token);
          if (data.refresh_token) {
            localStorage.setItem('refreshToken', data.refresh_token);
          }
          localStorage.setItem('userRole', data.user.role);
          localStorage.setItem('userId', data.user.id);
          localStorage.setItem('tenantId', data.user.tenant_id || '');
          localStorage.setItem('userEmail', data.user.email);
          localStorage.setItem('mustResetPassword', String(data.user.must_reset_password));
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('userRole');
        localStorage.removeItem('userId');
        localStorage.removeItem('tenantId');
        localStorage.removeItem('userEmail');
        localStorage.removeItem('mustResetPassword');
      }
    }
    return Promise.reject(error);
  }
);

export default api;
