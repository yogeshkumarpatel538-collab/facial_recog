import { Card, CardContent, Typography, Box, Skeleton } from '@mui/material';

export default function StatCard({ title, value, subtitle, icon, color = 'primary.main', loading }) {
  if (loading) {
    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Skeleton width="60%" />
          <Skeleton width="40%" height={48} sx={{ my: 1 }} />
          <Skeleton width="80%" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {title}
          </Typography>
          {icon && (
            <Box sx={{ color, opacity: 0.8 }}>{icon}</Box>
          )}
        </Box>
        <Typography variant="h4" fontWeight={700} sx={{ color, my: 1 }}>
          {value ?? '—'}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}
