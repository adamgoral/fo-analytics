import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Box } from '@mui/material';
import { MainLayout } from './components/layout';
import { ProtectedRoute, LoadingSpinner } from './components/common';
import { useAuth } from './hooks';
import LoginPage from './features/auth/LoginPage';
import DashboardPage from './features/dashboard/DashboardPage';
import DocumentsPage from './features/documents/DocumentsPage';
import StrategiesPage from './features/strategies/StrategiesPage';
import './App.css';

function App() {
  const { isAuthenticated, loading, refreshUser } = useAuth();

  // Initialize user data on app start if authenticated
  useEffect(() => {
    if (isAuthenticated) {
      refreshUser();
    }
  }, [isAuthenticated, refreshUser]);

  // Show loading spinner while checking authentication
  if (loading) {
    return <LoadingSpinner message="Loading application..." fullScreen />;
  }

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Routes>
        {/* Public routes */}
        <Route 
          path="/login" 
          element={
            isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />
          } 
        />
        
        {/* Protected routes with layout */}
        <Route 
          path="/*" 
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="documents" element={<DocumentsPage />} />
          <Route path="strategies" element={<StrategiesPage />} />
          <Route 
            path="backtests" 
            element={
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <h2>Backtests Page</h2>
                <p>Coming soon...</p>
              </Box>
            } 
          />
          <Route 
            path="analytics" 
            element={
              <ProtectedRoute requiredRole="analyst">
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <h2>Analytics Page</h2>
                  <p>Coming soon...</p>
                </Box>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="users" 
            element={
              <ProtectedRoute requiredRole="admin">
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <h2>User Management</h2>
                  <p>Coming soon...</p>
                </Box>
              </ProtectedRoute>
            } 
          />
          <Route 
            path="notifications" 
            element={
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <h2>Notifications</h2>
                <p>Coming soon...</p>
              </Box>
            } 
          />
          <Route 
            path="settings" 
            element={
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <h2>Settings</h2>
                <p>Coming soon...</p>
              </Box>
            } 
          />
          <Route 
            path="help" 
            element={
              <Box sx={{ p: 4, textAlign: 'center' }}>
                <h2>Help & Support</h2>
                <p>Coming soon...</p>
              </Box>
            } 
          />
        </Route>
      </Routes>
    </Box>
  );
}

export default App;
