import api from './axios';

export const usersApi = {
  list: () => api.get('/users').then((r) => r.data),

  create: (payload) => api.post('/users', payload).then((r) => r.data),
};
