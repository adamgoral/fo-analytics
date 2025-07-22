import React, { useState } from 'react';
import {
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  InputAdornment,
  IconButton,
  CircularProgress,
  Link,
  Divider,
  LinearProgress,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Email as EmailIcon,
  Lock as LockIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks';

interface RegisterFormProps {
  onSwitchToLogin?: () => void;
}

const RegisterForm: React.FC<RegisterFormProps> = ({ onSwitchToLogin }) => {
  const navigate = useNavigate();
  const { register, loading, error, clearError } = useAuth();
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const calculatePasswordStrength = (password: string): number => {
    let score = 0;
    if (password.length >= 8) score += 25;
    if (/[a-z]/.test(password)) score += 25;
    if (/[A-Z]/.test(password)) score += 25;
    if (/[0-9]/.test(password)) score += 25;
    return score;
  };

  const getPasswordStrengthColor = (strength: number): string => {
    if (strength < 25) return 'error';
    if (strength < 50) return 'warning';
    if (strength < 75) return 'info';
    return 'success';
  };

  const getPasswordStrengthLabel = (strength: number): string => {
    if (strength < 25) return 'Weak';
    if (strength < 50) return 'Fair';
    if (strength < 75) return 'Good';
    return 'Strong';
  };

  const validateForm = () => {
    const errors: Record<string, string> = {};
    
    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }
    
    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters long';
    }
    
    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    if (!formData.fullName.trim()) {
      errors.fullName = 'Full name is required';
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    clearError();
    
    if (!validateForm()) {
      return;
    }

    const success = await register({
      email: formData.email,
      password: formData.password,
      full_name: formData.fullName.trim(),
    });

    if (success) {
      navigate('/');
    }
  };

  const handleInputChange = (field: keyof typeof formData) => (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setFormData({
      ...formData,
      [field]: event.target.value,
    });
    
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors({
        ...validationErrors,
        [field]: '',
      });
    }
  };

  const passwordStrength = calculatePasswordStrength(formData.password);

  return (
    <Paper
      elevation={3}
      sx={{
        p: 4,
        maxWidth: 400,
        width: '100%',
        mx: 'auto',
        borderRadius: 2,
      }}
    >
      <Box sx={{ mb: 3, textAlign: 'center' }}>
        <Box
          sx={{
            width: 48,
            height: 48,
            bgcolor: 'primary.main',
            borderRadius: 1,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            mx: 'auto',
            mb: 2,
          }}
        >
          <Typography variant="h5" sx={{ color: 'white', fontWeight: 'bold' }}>
            FO
          </Typography>
        </Box>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
          Create account
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Join FO Analytics to get started
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          fullWidth
          label="Full Name"
          type="text"
          value={formData.fullName}
          onChange={handleInputChange('fullName')}
          error={Boolean(validationErrors.fullName)}
          helperText={validationErrors.fullName}
          disabled={loading}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <PersonIcon color="action" />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />

        <TextField
          fullWidth
          label="Email"
          type="email"
          value={formData.email}
          onChange={handleInputChange('email')}
          error={Boolean(validationErrors.email)}
          helperText={validationErrors.email}
          disabled={loading}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <EmailIcon color="action" />
              </InputAdornment>
            ),
          }}
          sx={{ mb: 2 }}
        />

        <TextField
          fullWidth
          label="Password"
          type={showPassword ? 'text' : 'password'}
          value={formData.password}
          onChange={handleInputChange('password')}
          error={Boolean(validationErrors.password)}
          helperText={validationErrors.password}
          disabled={loading}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <LockIcon color="action" />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setShowPassword(!showPassword)}
                  edge="end"
                  disabled={loading}
                >
                  {showPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{ mb: formData.password ? 1 : 2 }}
        />

        {formData.password && (
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
              <Typography variant="caption" color="text.secondary">
                Password strength
              </Typography>
              <Typography variant="caption" color={`${getPasswordStrengthColor(passwordStrength)}.main`}>
                {getPasswordStrengthLabel(passwordStrength)}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={passwordStrength}
              color={getPasswordStrengthColor(passwordStrength) as any}
              sx={{ height: 4, borderRadius: 2 }}
            />
          </Box>
        )}

        <TextField
          fullWidth
          label="Confirm Password"
          type={showConfirmPassword ? 'text' : 'password'}
          value={formData.confirmPassword}
          onChange={handleInputChange('confirmPassword')}
          error={Boolean(validationErrors.confirmPassword)}
          helperText={validationErrors.confirmPassword}
          disabled={loading}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <LockIcon color="action" />
              </InputAdornment>
            ),
            endAdornment: (
              <InputAdornment position="end">
                <IconButton
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  edge="end"
                  disabled={loading}
                >
                  {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                </IconButton>
              </InputAdornment>
            ),
          }}
          sx={{ mb: 3 }}
        />

        <Button
          type="submit"
          fullWidth
          variant="contained"
          size="large"
          disabled={loading}
          sx={{ mb: 2, height: 48 }}
        >
          {loading ? (
            <CircularProgress size={24} />
          ) : (
            'Create Account'
          )}
        </Button>

        {onSwitchToLogin && (
          <>
            <Divider sx={{ my: 2 }}>
              <Typography variant="body2" color="text.secondary">
                or
              </Typography>
            </Divider>

            <Typography variant="body2" align="center" color="text.secondary">
              Already have an account?{' '}
              <Link
                component="button"
                variant="body2"
                onClick={onSwitchToLogin}
                sx={{ textDecoration: 'none' }}
              >
                Sign in
              </Link>
            </Typography>
          </>
        )}
      </Box>
    </Paper>
  );
};

export default RegisterForm;