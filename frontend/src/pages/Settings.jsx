import {
  Box,
  Typography,
  Card,
  CardContent,
  Stack,
  Divider,
  List,
  ListItem,
  ListItemText,
  Switch,
  FormControlLabel,
  Button,
  Chip,
  CircularProgress,
} from '@mui/material';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import LightModeIcon from '@mui/icons-material/LightMode';
import LogoutIcon from '@mui/icons-material/Logout';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { useThemeMode } from '../context/ThemeContext';
import { systemApi } from '../api/system';

export default function Settings() {
  const { user, logout, isAdmin } = useAuth();
  const { mode, toggleMode } = useThemeMode();
  const navigate = useNavigate();

  const healthQuery = useQuery({
    queryKey: ['health'],
    queryFn: systemApi.health,
    refetchInterval: 60000,
  });

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isHealthy = healthQuery.data?.status === 'ok';

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body2" color="text.secondary" mb={3}>
        Manage your account and application preferences
      </Typography>

      <Stack spacing={3} maxWidth={600}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              System Status
            </Typography>
            {healthQuery.isLoading ? (
              <CircularProgress size={24} />
            ) : (
              <Stack direction="row" alignItems="center" gap={1}>
                {isHealthy ? (
                  <CheckCircleIcon color="success" fontSize="small" />
                ) : (
                  <ErrorOutlineIcon color="error" fontSize="small" />
                )}
                <Typography variant="body2">
                  Backend API:{' '}
                  <Chip
                    label={isHealthy ? 'Online' : 'Unreachable'}
                    size="small"
                    color={isHealthy ? 'success' : 'error'}
                  />
                </Typography>
              </Stack>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Account
            </Typography>
            <List disablePadding>
              <ListItem disableGutters>
                <ListItemText primary="Email" secondary={user?.email} />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="Role"
                  secondary={
                    <Chip
                      label={user?.role}
                      size="small"
                      color={isAdmin ? 'primary' : 'default'}
                      sx={{ mt: 0.5, textTransform: 'capitalize' }}
                    />
                  }
                />
              </ListItem>
              <ListItem disableGutters>
                <ListItemText
                  primary="Member since"
                  secondary={
                    user?.created_at
                      ? new Date(user.created_at).toLocaleDateString()
                      : '—'
                  }
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Appearance
            </Typography>
            <FormControlLabel
              control={<Switch checked={mode === 'dark'} onChange={toggleMode} />}
              label={
                <Stack direction="row" alignItems="center" gap={1}>
                  {mode === 'dark' ? <DarkModeIcon fontSize="small" /> : <LightModeIcon fontSize="small" />}
                  Dark mode
                </Stack>
              }
            />
          </CardContent>
        </Card>

        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Session
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={2}>
              Sign out of your current session. You will need to log in again.
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <Button
              variant="outlined"
              color="error"
              startIcon={<LogoutIcon />}
              onClick={handleLogout}
            >
              Logout
            </Button>
          </CardContent>
        </Card>
      </Stack>
    </Box>
  );
}
