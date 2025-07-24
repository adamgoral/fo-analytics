import React from 'react';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Typography,
  Box,
  Chip,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Description as DocumentsIcon,
  TrendingUp as StrategiesIcon,
  Assessment as BacktestIcon,
  Settings as SettingsIcon,
  People as UsersIcon,
  BarChart as AnalyticsIcon,
  Notifications as NotificationsIcon,
  Help as HelpIcon,
  SmartToy as AIChatIcon,
  PieChart as PortfolioIcon,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  width: number;
}

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ReactElement;
  path: string;
  badge?: number;
  roles?: ('admin' | 'analyst' | 'viewer')[];
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, width }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user } = useAuth();

  const navigationItems: NavigationItem[] = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/',
    },
    {
      id: 'documents',
      label: 'Documents',
      icon: <DocumentsIcon />,
      path: '/documents',
      badge: 3,
    },
    {
      id: 'strategies',
      label: 'Strategies',
      icon: <StrategiesIcon />,
      path: '/strategies',
      badge: 12,
    },
    {
      id: 'portfolio',
      label: 'Portfolio',
      icon: <PortfolioIcon />,
      path: '/portfolio',
    },
    {
      id: 'backtests',
      label: 'Backtests',
      icon: <BacktestIcon />,
      path: '/backtests',
    },
    {
      id: 'ai-chat',
      label: 'AI Chat',
      icon: <AIChatIcon />,
      path: '/ai-chat',
    },
    {
      id: 'analytics',
      label: 'Analytics',
      icon: <AnalyticsIcon />,
      path: '/analytics',
      roles: ['admin', 'analyst'],
    },
    {
      id: 'users',
      label: 'User Management',
      icon: <UsersIcon />,
      path: '/users',
      roles: ['admin'],
    },
  ];

  const secondaryItems: NavigationItem[] = [
    {
      id: 'notifications',
      label: 'Notifications',
      icon: <NotificationsIcon />,
      path: '/notifications',
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: <SettingsIcon />,
      path: '/settings',
    },
    {
      id: 'help',
      label: 'Help & Support',
      icon: <HelpIcon />,
      path: '/help',
    },
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
    onClose();
  };

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const canAccessItem = (item: NavigationItem) => {
    if (!item.roles) return true;
    return item.roles.includes(user?.role || 'viewer');
  };

  const drawer = (
    <Box>
      {/* Logo Section */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          borderBottom: '1px solid',
          borderColor: 'divider',
          minHeight: 64,
        }}
      >
        <Box
          sx={{
            width: 32,
            height: 32,
            bgcolor: 'primary.main',
            borderRadius: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>
            FO
          </Typography>
        </Box>
        <Box>
          <Typography variant="h6" sx={{ fontWeight: 600, lineHeight: 1.2 }}>
            Analytics
          </Typography>
          <Typography variant="caption" color="text.secondary">
            v1.0.0
          </Typography>
        </Box>
      </Box>

      {/* Main Navigation */}
      <List sx={{ pt: 2 }}>
        {navigationItems
          .filter(canAccessItem)
          .map((item) => (
            <ListItem key={item.id} disablePadding sx={{ px: 1 }}>
              <ListItemButton
                selected={isActive(item.path)}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  borderRadius: 2,
                  mx: 1,
                  '&.Mui-selected': {
                    bgcolor: 'primary.main',
                    color: 'primary.contrastText',
                    '&:hover': {
                      bgcolor: 'primary.dark',
                    },
                    '& .MuiListItemIcon-root': {
                      color: 'primary.contrastText',
                    },
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 40,
                    color: isActive(item.path) ? 'inherit' : 'action.active',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: '0.875rem',
                    fontWeight: isActive(item.path) ? 600 : 400,
                  }}
                />
                {item.badge && (
                  <Chip
                    label={item.badge}
                    size="small"
                    color={isActive(item.path) ? 'secondary' : 'primary'}
                    sx={{ 
                      minWidth: 20,
                      height: 20,
                      '& .MuiChip-label': { 
                        fontSize: '0.75rem',
                        px: 0.5 
                      }
                    }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          ))}
      </List>

      <Divider sx={{ my: 2 }} />

      {/* Secondary Navigation */}
      <List>
        {secondaryItems
          .filter(canAccessItem)
          .map((item) => (
            <ListItem key={item.id} disablePadding sx={{ px: 1 }}>
              <ListItemButton
                selected={isActive(item.path)}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  borderRadius: 2,
                  mx: 1,
                  '&.Mui-selected': {
                    bgcolor: 'action.selected',
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 40,
                    color: 'action.active',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText 
                  primary={item.label}
                  primaryTypographyProps={{
                    fontSize: '0.875rem',
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
      </List>

      {/* User Info at Bottom */}
      <Box
        sx={{
          position: 'absolute',
          bottom: 16,
          left: 16,
          right: 16,
          p: 2,
          bgcolor: 'background.paper',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 2,
        }}
      >
        <Typography variant="caption" color="text.secondary">
          Signed in as
        </Typography>
        <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
          {user?.full_name || user?.email}
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          <Chip
            label={user?.role?.toUpperCase()}
            size="small"
            color={user?.role === 'admin' ? 'error' : user?.role === 'analyst' ? 'primary' : 'secondary'}
            variant="outlined"
            sx={{ fontSize: '0.625rem' }}
          />
        </Box>
      </Box>
    </Box>
  );

  return (
    <Box component="nav" sx={{ width: { sm: width }, flexShrink: { sm: 0 } }}>
      {/* Mobile drawer */}
      <Drawer
        variant="temporary"
        open={isOpen}
        onClose={onClose}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: width,
          },
        }}
      >
        {drawer}
      </Drawer>

      {/* Desktop drawer */}
      <Drawer
        variant="persistent"
        open={isOpen}
        sx={{
          display: { xs: 'none', sm: 'block' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: width,
            position: 'relative',
            height: '100vh',
          },
        }}
      >
        {drawer}
      </Drawer>
    </Box>
  );
};

export default Sidebar;