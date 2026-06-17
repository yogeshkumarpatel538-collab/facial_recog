const TOKEN_KEY = 'pcs_access_token';
const REFRESH_KEY = 'pcs_refresh_token';
const THEME_KEY = 'pcs_theme_mode';

export const storage = {
  getAccessToken: () => localStorage.getItem(TOKEN_KEY),
  setAccessToken: (token) => localStorage.setItem(TOKEN_KEY, token),
  getRefreshToken: () => localStorage.getItem(REFRESH_KEY),
  setRefreshToken: (token) => localStorage.setItem(REFRESH_KEY, token),
  clearTokens: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
  getThemeMode: () => localStorage.getItem(THEME_KEY) || 'dark',
  setThemeMode: (mode) => localStorage.setItem(THEME_KEY, mode),
};

export function getWsUrl(token) {
  const base = import.meta.env.VITE_WS_BASE_URL ?? '';
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = base || `${protocol}//${window.location.host}`;
  return `${host}/ws/live-counts?token=${encodeURIComponent(token)}`;
}

export function formatHour(hour) {
  const period = hour >= 12 ? 'PM' : 'AM';
  const h = hour % 12 || 12;
  return `${h}:00 ${period}`;
}

export function formatMonth(year, month) {
  return new Date(year, month - 1).toLocaleString('default', {
    month: 'short',
    year: 'numeric',
  });
}

export function getErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg || d.message).join(', ');
  return error?.message || 'An unexpected error occurred';
}
