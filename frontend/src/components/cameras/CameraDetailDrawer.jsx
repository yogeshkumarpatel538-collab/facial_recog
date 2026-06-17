import {
  Drawer,
  Box,
  Typography,
  IconButton,
  Tabs,
  Tab,
  Chip,
  Stack,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Grid,
  CircularProgress,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { camerasApi } from '../../api/cameras';
import { analyticsApi } from '../../api/analytics';
import StatCard from '../common/StatCard';
import ErrorAlert from '../common/ErrorAlert';
import { getErrorMessage } from '../../utils/storage';
import { useLiveCountsContext } from '../../context/LiveCountsContext';

function TabPanel({ children, value, index }) {
  if (value !== index) return null;
  return <Box sx={{ pt: 2 }}>{children}</Box>;
}

export default function CameraDetailDrawer({ cameraId, open, onClose }) {
  const [tab, setTab] = useState(0);
  const { liveCounts } = useLiveCountsContext();

  const cameraQuery = useQuery({
    queryKey: ['cameras', cameraId],
    queryFn: () => camerasApi.get(cameraId),
    enabled: open && !!cameraId,
  });

  const analyticsQuery = useQuery({
    queryKey: ['analytics', 'camera', cameraId],
    queryFn: () => analyticsApi.camera(cameraId, { limit: 14 }),
    enabled: open && !!cameraId,
  });

  const eventsQuery = useQuery({
    queryKey: ['cameras', cameraId, 'events'],
    queryFn: () => camerasApi.events(cameraId, { limit: 50 }),
    enabled: open && !!cameraId && tab === 1,
  });

  const summariesQuery = useQuery({
    queryKey: ['cameras', cameraId, 'summaries'],
    queryFn: () => camerasApi.summaries(cameraId),
    enabled: open && !!cameraId && tab === 2,
  });

  const camera = cameraQuery.data;
  const analytics = analyticsQuery.data;
  const live = cameraId ? liveCounts[cameraId] : null;
  const error = cameraQuery.error || analyticsQuery.error || eventsQuery.error || summariesQuery.error;

  const handleClose = () => {
    setTab(0);
    onClose();
  };

  return (
    <Drawer anchor="right" open={open} onClose={handleClose} PaperProps={{ sx: { width: { xs: '100%', sm: 480 } } }}>
      <Box sx={{ p: 2, height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={1}>
          <Typography variant="h6" fontWeight={700}>
            Camera Details
          </Typography>
          <IconButton onClick={handleClose} edge="end">
            <CloseIcon />
          </IconButton>
        </Stack>

        {cameraQuery.isLoading ? (
          <Box display="flex" justifyContent="center" py={6}>
            <CircularProgress />
          </Box>
        ) : camera ? (
          <>
            <Typography variant="h5" fontWeight={600}>
              {camera.name}
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={1}>
              {camera.location}
            </Typography>
            <Stack direction="row" gap={1} mb={2}>
              <Chip
                label={camera.active ? 'Active' : 'Disabled'}
                color={camera.active ? 'success' : 'default'}
                size="small"
              />
              {live && (
                <>
                  <Chip label={`Live IN: ${live.total_in}`} color="success" size="small" variant="outlined" />
                  <Chip label={`Live OUT: ${live.total_out}`} color="error" size="small" variant="outlined" />
                </>
              )}
            </Stack>

            <Typography variant="caption" color="text.secondary" sx={{ wordBreak: 'break-all' }}>
              {camera.rtsp_url}
            </Typography>

            <Divider sx={{ my: 2 }} />

            <ErrorAlert error={error ? getErrorMessage(error) : null} />

            <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="fullWidth">
              <Tab label="Analytics" />
              <Tab label="Events" />
              <Tab label="Summaries" />
            </Tabs>

            <Box sx={{ flex: 1, overflow: 'auto' }}>
              <TabPanel value={tab} index={0}>
                {analyticsQuery.isLoading ? (
                  <Box display="flex" justifyContent="center" py={4}>
                    <CircularProgress size={28} />
                  </Box>
                ) : analytics ? (
                  <>
                    <Grid container spacing={2} mb={2}>
                      <Grid item xs={6}>
                        <StatCard
                          title="Period IN"
                          value={analytics.total_in}
                          icon={<LoginIcon fontSize="small" />}
                          color="success.main"
                        />
                      </Grid>
                      <Grid item xs={6}>
                        <StatCard
                          title="Period OUT"
                          value={analytics.total_out}
                          icon={<LogoutIcon fontSize="small" />}
                          color="error.main"
                        />
                      </Grid>
                    </Grid>
                    <Typography variant="body2" color="text.secondary" mb={2}>
                      {analytics.start_date} → {analytics.end_date}
                    </Typography>
                    <Typography variant="subtitle2" gutterBottom>
                      Daily breakdown
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Date</TableCell>
                            <TableCell align="right">IN</TableCell>
                            <TableCell align="right">OUT</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {(analytics.daily?.items || []).map((row) => (
                            <TableRow key={row.date}>
                              <TableCell>{row.date}</TableCell>
                              <TableCell align="right">{row.total_in}</TableCell>
                              <TableCell align="right">{row.total_out}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </>
                ) : null}
              </TabPanel>

              <TabPanel value={tab} index={1}>
                {eventsQuery.isLoading ? (
                  <Box display="flex" justifyContent="center" py={4}>
                    <CircularProgress size={28} />
                  </Box>
                ) : (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Time</TableCell>
                          <TableCell>Direction</TableCell>
                          <TableCell>Track</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {(eventsQuery.data || []).length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={3} align="center" sx={{ py: 3 }}>
                              <Typography variant="body2" color="text.secondary">
                                No events recorded
                              </Typography>
                            </TableCell>
                          </TableRow>
                        ) : (
                          eventsQuery.data.map((event) => (
                            <TableRow key={event.id}>
                              <TableCell>
                                {new Date(event.timestamp).toLocaleString()}
                              </TableCell>
                              <TableCell>
                                <Chip
                                  label={event.direction.toUpperCase()}
                                  size="small"
                                  color={event.direction === 'in' ? 'success' : 'error'}
                                />
                              </TableCell>
                              <TableCell>{event.track_id}</TableCell>
                            </TableRow>
                          ))
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </TabPanel>

              <TabPanel value={tab} index={2}>
                {summariesQuery.isLoading ? (
                  <Box display="flex" justifyContent="center" py={4}>
                    <CircularProgress size={28} />
                  </Box>
                ) : (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Date</TableCell>
                          <TableCell align="right">IN</TableCell>
                          <TableCell align="right">OUT</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {(summariesQuery.data || []).length === 0 ? (
                          <TableRow>
                            <TableCell colSpan={3} align="center" sx={{ py: 3 }}>
                              <Typography variant="body2" color="text.secondary">
                                No daily summaries
                              </Typography>
                            </TableCell>
                          </TableRow>
                        ) : (
                          summariesQuery.data
                            .slice()
                            .sort((a, b) => b.date.localeCompare(a.date))
                            .map((row) => (
                              <TableRow key={row.id}>
                                <TableCell>{row.date}</TableCell>
                                <TableCell align="right">{row.total_in}</TableCell>
                                <TableCell align="right">{row.total_out}</TableCell>
                              </TableRow>
                            ))
                        )}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </TabPanel>
            </Box>
          </>
        ) : null}
      </Box>
    </Drawer>
  );
}
