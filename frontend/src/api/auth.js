import api from './axios';

export const authApi = {
  login: (email, password) =>
    api.post('/auth/login', { email, password }).then((r) => r.data),

  register: (email, password) =>
    api.post('/auth/register', { email, password }).then((r) => r.data),

  me: () => api.get('/auth/me').then((r) => r.data),

  logout: (refreshToken) =>
    api.post('/auth/logout', { refresh_token: refreshToken }).then((r) => r.data),
};
