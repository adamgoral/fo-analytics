import React, { useState } from 'react';
import { Box, CssBaseline, Toolbar } from '@mui/material';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import Footer from './Footer';

const DRAWER_WIDTH = 280;

const MainLayout: React.FC = () => {
  const [isDrawerOpen, setIsDrawerOpen] = useState(true);

  const handleDrawerToggle = () => {
    setIsDrawerOpen(!isDrawerOpen);
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <CssBaseline />
      
      {/* Header */}
      <Header
        onMenuToggle={handleDrawerToggle}
        drawerWidth={DRAWER_WIDTH}
        isDrawerOpen={isDrawerOpen}
      />
      
      {/* Sidebar */}
      <Sidebar
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        width={DRAWER_WIDTH}
      />
      
      {/* Main Content */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          width: { sm: isDrawerOpen ? `calc(100% - ${DRAWER_WIDTH}px)` : '100%' },
          ml: { sm: isDrawerOpen ? `${DRAWER_WIDTH}px` : 0 },
          transition: 'width 0.3s ease, margin 0.3s ease',
          minHeight: '100vh',
        }}
      >
        {/* Toolbar spacer */}
        <Toolbar />
        
        {/* Page content */}
        <Box
          sx={{
            flexGrow: 1,
            p: 3,
            bgcolor: 'background.default',
          }}
        >
          <Outlet />
        </Box>
        
        {/* Footer */}
        <Footer 
          drawerWidth={DRAWER_WIDTH}
          isDrawerOpen={isDrawerOpen}
        />
      </Box>
    </Box>
  );
};

export default MainLayout;