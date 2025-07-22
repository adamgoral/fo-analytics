import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Badge,
  Menu,
  MenuItem,
  Avatar,
  Box,
  Divider,
  ListItemIcon,
  ListItemText,
  Chip,
  Button,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useAuth } from '../../hooks';

interface HeaderProps {
  onMenuToggle: () => void;
  drawerWidth: number;
  isDrawerOpen: boolean;
}

const Header: React.FC<HeaderProps> = ({ onMenuToggle, drawerWidth, isDrawerOpen }) => {
  const { user, logout } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [notificationAnchor, setNotificationAnchor] = useState<null | HTMLElement>(null);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleProfileMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNotificationOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchor(event.currentTarget);
  };

  const handleNotificationClose = () => {
    setNotificationAnchor(null);
  };

  const handleLogout = () => {
    logout();
    handleProfileMenuClose();
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'error';
      case 'analyst':
        return 'primary';
      case 'viewer':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'admin':
        return 'Administrator';
      case 'analyst':
        return 'Analyst';
      case 'viewer':
        return 'Viewer';
      default:
        return 'User';
    }
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        width: { sm: isDrawerOpen ? `calc(100% - ${drawerWidth}px)` : '100%' },
        ml: { sm: isDrawerOpen ? `${drawerWidth}px` : 0 },
        transition: 'width 0.3s ease, margin 0.3s ease',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={onMenuToggle}
          sx={{ mr: 2 }}
        >
          <MenuIcon />
        </IconButton>

        <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
          FO Analytics
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* System Status */}
          <Chip
            label="System Online"
            color="success"
            size="small"
            variant="outlined"
            sx={{ 
              borderColor: 'rgba(255, 255, 255, 0.3)',
              color: 'rgba(255, 255, 255, 0.9)',
              display: { xs: 'none', md: 'inline-flex' }
            }}
          />

          {/* Notifications */}
          <IconButton
            size="large"
            aria-label="notifications"
            color="inherit"
            onClick={handleNotificationOpen}
          >
            <Badge badgeContent={3} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>

          {/* User Profile */}
          <Button
            onClick={handleProfileMenuOpen}
            sx={{ 
              color: 'inherit', 
              textTransform: 'none',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              borderRadius: 2,
              px: 2,
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
              }
            }}
          >
            <Avatar
              sx={{ 
                width: 32, 
                height: 32, 
                bgcolor: 'primary.dark',
                fontSize: '0.875rem'
              }}
            >
              {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
            </Avatar>
            <Box sx={{ display: { xs: 'none', sm: 'block' }, textAlign: 'left' }}>
              <Typography variant="body2" sx={{ lineHeight: 1.2 }}>
                {user?.full_name || user?.email}
              </Typography>
              <Chip 
                label={getRoleLabel(user?.role || '')}
                size="small"
                color={getRoleColor(user?.role || '') as any}
                sx={{ 
                  height: 16,
                  fontSize: '0.625rem',
                  '& .MuiChip-label': { px: 0.5 }
                }}
              />
            </Box>
          </Button>
        </Box>

        {/* Profile Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleProfileMenuClose}
          onClick={handleProfileMenuClose}
          PaperProps={{
            elevation: 3,
            sx: {
              mt: 1.5,
              minWidth: 220,
              '& .MuiAvatar-root': {
                width: 24,
                height: 24,
                ml: -0.5,
                mr: 1,
              },
            },
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Signed in as
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 500 }}>
              {user?.full_name || user?.email}
            </Typography>
            <Chip 
              label={getRoleLabel(user?.role || '')}
              size="small"
              color={getRoleColor(user?.role || '') as any}
              sx={{ mt: 0.5 }}
            />
          </Box>
          
          <Divider />
          
          <MenuItem onClick={handleProfileMenuClose}>
            <ListItemIcon>
              <PersonIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>My Profile</ListItemText>
          </MenuItem>
          
          <MenuItem onClick={handleProfileMenuClose}>
            <ListItemIcon>
              <SettingsIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Settings</ListItemText>
          </MenuItem>
          
          <Divider />
          
          <MenuItem onClick={handleLogout}>
            <ListItemIcon>
              <LogoutIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Sign Out</ListItemText>
          </MenuItem>
        </Menu>

        {/* Notification Menu */}
        <Menu
          anchorEl={notificationAnchor}
          open={Boolean(notificationAnchor)}
          onClose={handleNotificationClose}
          PaperProps={{
            elevation: 3,
            sx: { mt: 1.5, minWidth: 300 },
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="h6">Notifications</Typography>
          </Box>
          <Divider />
          <MenuItem onClick={handleNotificationClose}>
            <ListItemText 
              primary="Strategy extraction completed"
              secondary="Document 'Q3 Trading Strategy.pdf' processed successfully"
            />
          </MenuItem>
          <MenuItem onClick={handleNotificationClose}>
            <ListItemText 
              primary="Backtest failed"
              secondary="Strategy 'Momentum Alpha' failed validation"
            />
          </MenuItem>
          <MenuItem onClick={handleNotificationClose}>
            <ListItemText 
              primary="New document uploaded"
              secondary="Analyst uploaded 'Market Analysis Q4.pdf'"
            />
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Header;