import api from './axios';

export const analyticsApi = {
  today: (params = {}) =>
    api.get('/analytics/today', { params }).then((r) => r.data),

  hourly: (params = {}) =>
    api.get('/analytics/hourly', { params }).then((r) => r.data),

  daily: (params = {}) =>
    api.get('/analytics/daily', { params }).then((r) => r.data),

  monthly: (params = {}) =>
    api.get('/analytics/monthly', { params }).then((r) => r.data),

  camera: (id, params = {}) =>
    api.get(`/analytics/camera/${id}`, { params }).then((r) => r.data),
};
