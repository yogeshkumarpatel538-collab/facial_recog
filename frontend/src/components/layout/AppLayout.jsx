import { useState } from 'react';
import { Box, Container, Toolbar } from '@mui/material';
import Sidebar, { DRAWER_WIDTH } from './Sidebar';
import TopBar from './TopBar';
import { LiveCountsProvider, useLiveCountsContext } from '../../context/LiveCountsContext';

function AppLayoutContent({ children, mobileOpen, setMobileOpen }) {
  const { connected } = useLiveCountsContext();

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { md: `calc(100% - ${DRAWER_WIDTH}px)` },
          minHeight: '100vh',
          bgcolor: 'background.default',
        }}
      >
        <TopBar onMenuClick={() => setMobileOpen(true)} wsConnected={connected} />
        <Toolbar sx={{ display: { md: 'none' } }} />
        <Container maxWidth="xl" sx={{ py: 3, px: { xs: 2, sm: 3 } }}>
          {children}
        </Container>
      </Box>
    </Box>
  );
}

export default function AppLayout({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <LiveCountsProvider>
      <AppLayoutContent mobileOpen={mobileOpen} setMobileOpen={setMobileOpen}>
        {children}
      </AppLayoutContent>
    </LiveCountsProvider>
  );
}
