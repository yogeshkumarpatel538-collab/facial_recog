import api from './axios';

export const camerasApi = {
  list: (activeOnly = false) =>
    api.get('/cameras', { params: { active_only: activeOnly } }).then((r) => r.data),

  get: (id) => api.get(`/cameras/${id}`).then((r) => r.data),

  create: (payload) => api.post('/cameras', payload).then((r) => r.data),

  update: (id, payload) => api.patch(`/cameras/${id}`, payload).then((r) => r.data),

  replace: (id, payload) => api.put(`/cameras/${id}`, payload).then((r) => r.data),

  delete: (id) => api.delete(`/cameras/${id}`),

  enable: (id) => api.patch(`/cameras/${id}/enable`).then((r) => r.data),

  disable: (id) => api.patch(`/cameras/${id}/disable`).then((r) => r.data),

  events: (id, params = {}) =>
    api.get(`/cameras/${id}/events`, { params }).then((r) => r.data),

  summaries: (id) => api.get(`/cameras/${id}/summaries`).then((r) => r.data),
};
