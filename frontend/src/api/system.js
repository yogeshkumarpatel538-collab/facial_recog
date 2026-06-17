import api from './axios';

export const systemApi = {
  health: () => api.get('/health').then((r) => r.data),
};
