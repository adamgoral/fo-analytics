import React from 'react';
import {
  Box,
  Typography,
  Chip,
  Divider,
  Link,
} from '@mui/material';
import {
  Circle as CircleIcon,
} from '@mui/icons-material';

interface FooterProps {
  drawerWidth: number;
  isDrawerOpen: boolean;
}

const Footer: React.FC<FooterProps> = ({ drawerWidth, isDrawerOpen }) => {
  const currentYear = new Date().getFullYear();

  // Mock system status - in real app this would come from API/websocket
  const systemStatus = {
    api: 'operational',
    database: 'operational', 
    llm: 'operational',
    queue: 'operational',
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'operational':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'down':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    const color = getStatusColor(status);
    return (
      <CircleIcon 
        sx={{ 
          fontSize: 8, 
          color: color === 'success' ? 'success.main' : 
                 color === 'warning' ? 'warning.main' : 
                 color === 'error' ? 'error.main' : 'grey.500'
        }} 
      />
    );
  };

  return (
    <Box
      component="footer"
      sx={{
        width: { sm: isDrawerOpen ? `calc(100% - ${drawerWidth}px)` : '100%' },
        ml: { sm: isDrawerOpen ? `${drawerWidth}px` : 0 },
        transition: 'width 0.3s ease, margin 0.3s ease',
        mt: 'auto',
        py: 2,
        px: 3,
        bgcolor: 'background.paper',
        borderTop: '1px solid',
        borderColor: 'divider',
      }}
    >
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: { xs: 'flex-start', md: 'center' },
          flexDirection: { xs: 'column', md: 'row' },
          gap: { xs: 2, md: 1 }
        }}
      >
        {/* Left side - Copyright and links */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="body2" color="text.secondary">
            © {currentYear} FO Analytics. All rights reserved.
          </Typography>
          <Box sx={{ display: { xs: 'none', sm: 'flex' }, alignItems: 'center', gap: 1 }}>
            <Link 
              href="/privacy" 
              variant="body2" 
              color="text.secondary"
              sx={{ textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
            >
              Privacy
            </Link>
            <Typography variant="body2" color="text.disabled">•</Typography>
            <Link 
              href="/terms" 
              variant="body2" 
              color="text.secondary"
              sx={{ textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
            >
              Terms
            </Link>
            <Typography variant="body2" color="text.disabled">•</Typography>
            <Link 
              href="/support" 
              variant="body2" 
              color="text.secondary"
              sx={{ textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
            >
              Support
            </Link>
          </Box>
        </Box>

        {/* Right side - System Status */}
        <Box 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 2,
            flexWrap: 'wrap'
          }}
        >
          <Typography 
            variant="body2" 
            color="text.secondary"
            sx={{ display: { xs: 'none', md: 'block' } }}
          >
            System Status:
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <Chip
              icon={getStatusIcon(systemStatus.api)}
              label="API"
              size="small"
              variant="outlined"
              color={getStatusColor(systemStatus.api) as any}
              sx={{ 
                height: 24,
                fontSize: '0.75rem',
                '& .MuiChip-icon': { ml: 0.5 }
              }}
            />
            
            <Chip
              icon={getStatusIcon(systemStatus.database)}
              label="DB"
              size="small"
              variant="outlined"
              color={getStatusColor(systemStatus.database) as any}
              sx={{ 
                height: 24,
                fontSize: '0.75rem',
                '& .MuiChip-icon': { ml: 0.5 }
              }}
            />
            
            <Chip
              icon={getStatusIcon(systemStatus.llm)}
              label="AI"
              size="small"
              variant="outlined"
              color={getStatusColor(systemStatus.llm) as any}
              sx={{ 
                height: 24,
                fontSize: '0.75rem',
                '& .MuiChip-icon': { ml: 0.5 }
              }}
            />
            
            <Chip
              icon={getStatusIcon(systemStatus.queue)}
              label="Queue"
              size="small"
              variant="outlined"
              color={getStatusColor(systemStatus.queue) as any}
              sx={{ 
                height: 24,
                fontSize: '0.75rem',
                '& .MuiChip-icon': { ml: 0.5 }
              }}
            />
          </Box>

          <Divider orientation="vertical" flexItem sx={{ height: 20, display: { xs: 'none', md: 'block' } }} />
          
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
            v1.0.0
          </Typography>
        </Box>
      </Box>
    </Box>
  );
};

export default Footer;