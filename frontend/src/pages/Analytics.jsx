import { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  TextField,
} from '@mui/material';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics';
import { camerasApi } from '../api/cameras';
import StatCard from '../components/common/StatCard';
import LoadingScreen from '../components/common/LoadingScreen';
import ErrorAlert from '../components/common/ErrorAlert';
import { formatHour, formatMonth, getErrorMessage } from '../utils/storage';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';

const CHART_COLORS = {
  in: '#10b981',
  out: '#ef4444',
};

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export default function Analytics() {
  const [cameraId, setCameraId] = useState('');
  const [selectedDate, setSelectedDate] = useState(todayIso());
  const [year, setYear] = useState(new Date().getFullYear());

  const params = cameraId ? { camera_id: Number(cameraId) } : {};

  const camerasQuery = useQuery({
    queryKey: ['cameras'],
    queryFn: () => camerasApi.list(),
  });

  const todayQuery = useQuery({
    queryKey: ['analytics', 'today', cameraId, selectedDate],
    queryFn: () => analyticsApi.today({ ...params, date: selectedDate }),
  });

  const cameraAnalyticsQuery = useQuery({
    queryKey: ['analytics', 'camera', cameraId],
    queryFn: () => analyticsApi.camera(Number(cameraId), { limit: 30 }),
    enabled: !!cameraId,
  });

  const hourlyQuery = useQuery({
    queryKey: ['analytics', 'hourly', cameraId, selectedDate],
    queryFn: () => analyticsApi.hourly({ ...params, date: selectedDate, limit: 24 }),
  });

  const dailyQuery = useQuery({
    queryKey: ['analytics', 'daily', cameraId],
    queryFn: () => analyticsApi.daily({ ...params, limit: 30 }),
  });

  const monthlyQuery = useQuery({
    queryKey: ['analytics', 'monthly', cameraId, year],
    queryFn: () => analyticsApi.monthly({ ...params, year, limit: 12 }),
  });

  const isLoading =
    hourlyQuery.isLoading || dailyQuery.isLoading || monthlyQuery.isLoading || todayQuery.isLoading;
  const error =
    hourlyQuery.error ||
    dailyQuery.error ||
    monthlyQuery.error ||
    todayQuery.error ||
    cameraAnalyticsQuery.error;

  const hourlyData = (hourlyQuery.data?.items || []).map((item) => ({
    ...item,
    label: formatHour(item.hour),
  }));

  const dailyData = (dailyQuery.data?.items || [])
    .slice()
    .reverse()
    .map((item) => ({
      ...item,
      label: item.date,
    }));

  const monthlyData = (monthlyQuery.data?.items || [])
    .slice()
    .reverse()
    .map((item) => ({
      ...item,
      label: formatMonth(item.year, item.month),
    }));

  const today = todayQuery.data;
  const cameraAnalytics = cameraAnalyticsQuery.data;

  if (isLoading) return <LoadingScreen message="Loading analytics..." />;

  return (
    <Box>
      <Stack
        direction={{ xs: 'column', sm: 'row' }}
        justifyContent="space-between"
        alignItems={{ sm: 'center' }}
        mb={3}
        gap={2}
      >
        <Box>
          <Typography variant="h4" gutterBottom>
            Analytics
          </Typography>
          <Typography variant="body2" color="text.secondary">
            IN/OUT trends across time periods
          </Typography>
        </Box>

        <Stack direction={{ xs: 'column', sm: 'row' }} gap={2}>
          <TextField
            label="Date"
            type="date"
            size="small"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
            sx={{ minWidth: 160 }}
          />
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Camera</InputLabel>
            <Select value={cameraId} label="Camera" onChange={(e) => setCameraId(e.target.value)}>
              <MenuItem value="">All Cameras</MenuItem>
              {(camerasQuery.data || []).map((cam) => (
                <MenuItem key={cam.id} value={String(cam.id)}>
                  {cam.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField
            label="Year"
            type="number"
            size="small"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            sx={{ width: 120 }}
            inputProps={{ min: 2000, max: 2100 }}
          />
        </Stack>
      </Stack>

      <ErrorAlert error={error ? getErrorMessage(error) : null} />

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={`IN (${selectedDate})`}
            value={today?.total_in ?? 0}
            icon={<LoginIcon />}
            color="success.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title={`OUT (${selectedDate})`}
            value={today?.total_out ?? 0}
            icon={<LogoutIcon />}
            color="error.main"
          />
        </Grid>
        {cameraAnalytics && (
          <>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title={`${cameraAnalytics.camera_name} IN`}
                value={cameraAnalytics.total_in}
                subtitle={`${cameraAnalytics.start_date} → ${cameraAnalytics.end_date}`}
                color="success.main"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title={`${cameraAnalytics.camera_name} OUT`}
                value={cameraAnalytics.total_out}
                color="error.main"
              />
            </Grid>
          </>
        )}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <ChartCard title={`Hourly IN/OUT (${selectedDate})`}>
            {hourlyData.length === 0 ? (
              <EmptyChart message="No hourly data for this date" />
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={hourlyData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="label" fontSize={12} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="total_in" name="IN" fill={CHART_COLORS.in} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="total_out" name="OUT" fill={CHART_COLORS.out} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </Grid>

        <Grid item xs={12} lg={6}>
          <ChartCard title="Daily IN/OUT (Last 30 Days)">
            {dailyData.length === 0 ? (
              <EmptyChart message="No daily data available" />
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={dailyData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="label" fontSize={11} angle={-45} textAnchor="end" height={60} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="total_in" name="IN" stroke={CHART_COLORS.in} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="total_out" name="OUT" stroke={CHART_COLORS.out} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </Grid>

        <Grid item xs={12} lg={6}>
          <ChartCard title={`Monthly Trend (${year})`}>
            {monthlyData.length === 0 ? (
              <EmptyChart message="No monthly data for this year" />
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="label" fontSize={12} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="total_in" name="IN" fill={CHART_COLORS.in} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="total_out" name="OUT" fill={CHART_COLORS.out} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>
        </Grid>
      </Grid>
    </Box>
  );
}

function ChartCard({ title, children }) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        {children}
      </CardContent>
    </Card>
  );
}

function EmptyChart({ message }) {
  return (
    <Box display="flex" alignItems="center" justifyContent="center" height={300}>
      <Typography variant="body2" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
}
