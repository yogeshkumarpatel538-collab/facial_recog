import {
  AppBar,
  Toolbar,
  IconButton,
  Typography,
  Box,
  Chip,
  Avatar,
  Menu,
  MenuItem,
  Tooltip,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import CircleIcon from '@mui/icons-material/Circle';
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useThemeMode } from '../../context/ThemeContext';
import { useNavigate } from 'react-router-dom';

export default function TopBar({ onMenuClick, wsConnected }) {
  const { user, logout } = useAuth();
  const { mode, toggleMode } = useThemeMode();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <AppBar
      position="sticky"
      elevation={0}
      sx={{
        bgcolor: 'background.paper',
        color: 'text.primary',
        borderBottom: 1,
        borderColor: 'divider',
      }}
    >
      <Toolbar>
        <IconButton edge="start" onClick={onMenuClick} sx={{ mr: 2, display: { md: 'none' } }}>
          <MenuIcon />
        </IconButton>

        <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 600 }}>
          People Counting System
        </Typography>

        <Box display="flex" alignItems="center" gap={1}>
          <Chip
            size="small"
            icon={
              <CircleIcon
                sx={{ fontSize: 10, color: wsConnected ? 'success.main' : 'text.disabled' }}
              />
            }
            label={wsConnected ? 'Live' : 'Offline'}
            variant="outlined"
            sx={{ display: { xs: 'none', sm: 'flex' } }}
          />

          <Tooltip title={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}>
            <IconButton onClick={toggleMode} color="inherit">
              {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
            </IconButton>
          </Tooltip>

          <IconButton onClick={(e) => setAnchorEl(e.currentTarget)}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main', fontSize: 14 }}>
              {user?.email?.[0]?.toUpperCase() || 'U'}
            </Avatar>
          </IconButton>

          <Menu anchorEl={anchorEl} open={!!anchorEl} onClose={() => setAnchorEl(null)}>
            <MenuItem disabled>{user?.email}</MenuItem>
            <MenuItem disabled sx={{ textTransform: 'capitalize' }}>
              Role: {user?.role}
            </MenuItem>
            <MenuItem
              onClick={() => {
                setAnchorEl(null);
                navigate('/settings');
              }}
            >
              Settings
            </MenuItem>
            <MenuItem onClick={handleLogout}>Logout</MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
