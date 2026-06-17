import { createTheme } from '@mui/material/styles';

export function createAppTheme(mode) {
  const isDark = mode === 'dark';

  return createTheme({
    palette: {
      mode,
      primary: {
        main: isDark ? '#6366f1' : '#4f46e5',
        light: isDark ? '#818cf8' : '#6366f1',
        dark: isDark ? '#4338ca' : '#3730a3',
      },
      secondary: {
        main: isDark ? '#22d3ee' : '#0891b2',
      },
      success: { main: '#10b981' },
      error: { main: '#ef4444' },
      warning: { main: '#f59e0b' },
      background: {
        default: isDark ? '#0f172a' : '#f1f5f9',
        paper: isDark ? '#1e293b' : '#ffffff',
      },
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h4: { fontWeight: 700 },
      h5: { fontWeight: 600 },
      h6: { fontWeight: 600 },
    },
    shape: { borderRadius: 12 },
    components: {
      MuiButton: {
        styleOverrides: {
          root: { textTransform: 'none', fontWeight: 600 },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            boxShadow: isDark
              ? '0 4px 24px rgba(0,0,0,0.4)'
              : '0 4px 24px rgba(0,0,0,0.06)',
          },
        },
      },
      MuiDrawer: {
        styleOverrides: {
          paper: {
            borderRight: isDark ? '1px solid #334155' : '1px solid #e2e8f0',
          },
        },
      },
    },
  });
}
