import { useMemo } from 'react';
import { Grid, Typography, Card, CardContent, Box, Chip, Button, Stack } from '@mui/material';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import VideocamIcon from '@mui/icons-material/Videocam';
import PeopleIcon from '@mui/icons-material/People';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { useQuery } from '@tanstack/react-query';
import { Link as RouterLink } from 'react-router-dom';
import StatCard from '../components/common/StatCard';
import LoadingScreen from '../components/common/LoadingScreen';
import ErrorAlert from '../components/common/ErrorAlert';
import { analyticsApi } from '../api/analytics';
import { camerasApi } from '../api/cameras';
import { useLiveCountsContext } from '../context/LiveCountsContext';
import { getErrorMessage } from '../utils/storage';

export default function Dashboard() {
  const { liveCounts, connected } = useLiveCountsContext();

  const todayQuery = useQuery({
    queryKey: ['analytics', 'today'],
    queryFn: () => analyticsApi.today(),
    refetchInterval: 60000,
  });

  const camerasQuery = useQuery({
    queryKey: ['cameras'],
    queryFn: () => camerasApi.list(),
    refetchInterval: 30000,
  });

  const today = todayQuery.data;
  const cameras = camerasQuery.data || [];
  const activeCameras = cameras.filter((c) => c.active).length;

  const occupancy = useMemo(() => {
    if (!today) return 0;
    return Math.max(today.total_in - today.total_out, 0);
  }, [today]);

  const isLoading = todayQuery.isLoading || camerasQuery.isLoading;
  const error = todayQuery.error || camerasQuery.error;

  if (isLoading) return <LoadingScreen message="Loading dashboard..." />;

  return (
    <Box>
      <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ sm: 'center' }} mb={3} gap={2}>
        <Box>
          <Typography variant="h4" gutterBottom>
            Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Real-time overview of people counting across all cameras
            {today?.date && ` · ${today.date}`}
          </Typography>
        </Box>
        <Chip
          label={connected ? 'Live feed connected' : 'Live feed reconnecting…'}
          color={connected ? 'success' : 'default'}
          variant="outlined"
        />
      </Stack>

      <ErrorAlert error={error ? getErrorMessage(error) : null} />

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Today's IN"
            value={today?.total_in ?? 0}
            icon={<LoginIcon />}
            color="success.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Today's OUT"
            value={today?.total_out ?? 0}
            icon={<LogoutIcon />}
            color="error.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Active Cameras"
            value={`${activeCameras} / ${cameras.length}`}
            icon={<VideocamIcon />}
            color="primary.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Current Occupancy"
            value={occupancy}
            subtitle="IN − OUT (today)"
            icon={<PeopleIcon />}
            color="secondary.main"
          />
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Camera Status</Typography>
            <Button component={RouterLink} to="/cameras" size="small" endIcon={<VisibilityIcon />}>
              Manage
            </Button>
          </Stack>

          {cameras.length === 0 ? (
            <Box textAlign="center" py={4}>
              <VideocamIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
              <Typography color="text.secondary" gutterBottom>
                No cameras configured yet
              </Typography>
              <Button component={RouterLink} to="/cameras" variant="outlined" size="small">
                Add your first camera
              </Button>
            </Box>
          ) : (
            <Grid container spacing={2}>
              {cameras.map((camera) => {
                const counts = liveCounts[camera.id];
                return (
                  <Grid item xs={12} sm={6} md={4} key={camera.id}>
                    <Card
                      variant="outlined"
                      sx={{
                        height: '100%',
                        opacity: camera.active ? 1 : 0.7,
                        borderColor: camera.active ? 'divider' : 'action.disabled',
                      }}
                    >
                      <CardContent>
                        <Stack direction="row" justifyContent="space-between" alignItems="flex-start" mb={1}>
                          <Typography fontWeight={600}>{camera.name}</Typography>
                          <Chip
                            label={camera.active ? 'Active' : 'Off'}
                            color={camera.active ? 'success' : 'default'}
                            size="small"
                          />
                        </Stack>
                        <Typography variant="body2" color="text.secondary" mb={1.5}>
                          {camera.location || 'No location set'}
                        </Typography>
                        <Stack direction="row" gap={1} flexWrap="wrap">
                          <Chip
                            label={`IN: ${counts?.total_in ?? '—'}`}
                            color="success"
                            size="small"
                            variant={counts ? 'filled' : 'outlined'}
                          />
                          <Chip
                            label={`OUT: ${counts?.total_out ?? '—'}`}
                            color="error"
                            size="small"
                            variant={counts ? 'filled' : 'outlined'}
                          />
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
