import { useCallback, useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '../store';
import {
  loginUser,
  registerUser,
  getCurrentUser,
  changePassword,
  logout,
  clearError,
  selectUser,
  selectIsAuthenticated,
  selectAuthLoading,
  selectAuthError,
} from '../store/slices/authSlice';
import type { LoginCredentials, RegisterData } from '../types';

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const user = useAppSelector(selectUser);
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  const loading = useAppSelector(selectAuthLoading);
  const error = useAppSelector(selectAuthError);

  // Initialize user data on mount if authenticated
  useEffect(() => {
    if (isAuthenticated && !user) {
      dispatch(getCurrentUser());
    }
  }, [isAuthenticated, user, dispatch]);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      const result = await dispatch(loginUser(credentials));
      return result.type === loginUser.fulfilled.type;
    },
    [dispatch]
  );

  const register = useCallback(
    async (userData: RegisterData) => {
      const result = await dispatch(registerUser(userData));
      return result.type === registerUser.fulfilled.type;
    },
    [dispatch]
  );

  const updatePassword = useCallback(
    async (oldPassword: string, newPassword: string) => {
      const result = await dispatch(changePassword({ oldPassword, newPassword }));
      return result.type === changePassword.fulfilled.type;
    },
    [dispatch]
  );

  const signOut = useCallback(() => {
    dispatch(logout());
  }, [dispatch]);

  const clearAuthError = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  const refreshUser = useCallback(() => {
    dispatch(getCurrentUser());
  }, [dispatch]);

  return {
    // State
    user,
    isAuthenticated,
    loading,
    error,
    
    // Actions
    login,
    register,
    logout: signOut,
    updatePassword,
    clearError: clearAuthError,
    refreshUser,
    
    // User role checks
    isAdmin: user?.role === 'admin',
    isAnalyst: user?.role === 'analyst',
    isViewer: user?.role === 'viewer',
    
    // Permission checks
    canManageUsers: user?.role === 'admin',
    canUploadDocuments: user?.role === 'admin' || user?.role === 'analyst',
    canViewStrategies: Boolean(user),
  };
};