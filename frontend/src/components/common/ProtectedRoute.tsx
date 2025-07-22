import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { useAuth } from '../../hooks';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'analyst' | 'viewer';
  requireAuth?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole,
  requireAuth = true 
}) => {
  const { isAuthenticated, user, loading } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          gap: 2,
        }}
      >
        <CircularProgress size={40} />
        <Typography variant="body2" color="text.secondary">
          Checking authentication...
        </Typography>
      </Box>
    );
  }

  // Redirect to login if authentication is required but user is not authenticated
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role-based access
  if (requiredRole && user) {
    const hasAccess = (() => {
      switch (requiredRole) {
        case 'admin':
          return user.role === 'admin';
        case 'analyst':
          return user.role === 'admin' || user.role === 'analyst';
        case 'viewer':
          return ['admin', 'analyst', 'viewer'].includes(user.role);
        default:
          return true;
      }
    })();

    if (!hasAccess) {
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '200px',
            textAlign: 'center',
            p: 4,
          }}
        >
          <Typography variant="h5" sx={{ mb: 2 }}>
            Access Denied
          </Typography>
          <Typography variant="body1" color="text.secondary">
            You don't have permission to access this page.
            {requiredRole && ` This page requires ${requiredRole} role.`}
          </Typography>
        </Box>
      );
    }
  }

  return <>{children}</>;
};

export default ProtectedRoute;