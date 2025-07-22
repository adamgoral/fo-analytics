import React, { useState } from 'react';
import { Box, Paper, Tabs, Tab } from '@mui/material';
import { LoginForm, RegisterForm } from '../../components/auth';

const LoginPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        bgcolor: 'background.default',
        py: 4,
        px: 2,
      }}
    >
      <Box sx={{ width: '100%', maxWidth: 400 }}>
        <Paper sx={{ mb: 2 }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            variant="fullWidth"
            sx={{ borderBottom: 1, borderColor: 'divider' }}
          >
            <Tab label="Sign In" />
            <Tab label="Sign Up" />
          </Tabs>
        </Paper>

        {activeTab === 0 ? (
          <LoginForm onSwitchToRegister={() => setActiveTab(1)} />
        ) : (
          <RegisterForm onSwitchToLogin={() => setActiveTab(0)} />
        )}
      </Box>
    </Box>
  );
};

export default LoginPage;