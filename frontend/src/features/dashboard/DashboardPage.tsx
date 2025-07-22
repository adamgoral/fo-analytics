import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  Avatar,
  Button,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  Chip,
  LinearProgress,
} from '@mui/material';
import {
  Upload as UploadIcon,
  Description as DocumentIcon,
  TrendingUp as StrategyIcon,
  Assessment as BacktestIcon,
  PlayArrow as PlayIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import { useAuth } from '../../hooks';
import { useNavigate } from 'react-router-dom';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Mock data - in real app this would come from API
  const stats = {
    totalDocuments: 24,
    totalStrategies: 89,
    totalBacktests: 156,
    successRate: 85,
  };

  const recentActivity = [
    {
      id: 1,
      type: 'document',
      title: 'Q4 Trading Strategy.pdf',
      status: 'completed',
      time: '2 hours ago',
    },
    {
      id: 2,
      type: 'strategy',
      title: 'Momentum Alpha Strategy',
      status: 'processing',
      time: '4 hours ago',
    },
    {
      id: 3,
      type: 'backtest',
      title: 'Mean Reversion Strategy',
      status: 'failed',
      time: '6 hours ago',
    },
    {
      id: 4,
      type: 'document',
      title: 'Market Analysis Q3.pdf',
      status: 'completed',
      time: '1 day ago',
    },
  ];

  const quickActions = [
    {
      title: 'Upload Document',
      description: 'Upload a new trading document for analysis',
      icon: <UploadIcon />,
      action: () => navigate('/documents'),
      color: 'primary',
    },
    {
      title: 'View Strategies',
      description: 'Browse extracted trading strategies',
      icon: <StrategyIcon />,
      action: () => navigate('/strategies'),
      color: 'success',
    },
    {
      title: 'Run Backtest',
      description: 'Test your strategies with historical data',
      icon: <PlayIcon />,
      action: () => navigate('/backtests'),
      color: 'info',
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckIcon color="success" />;
      case 'processing':
        return <ScheduleIcon color="warning" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      default:
        return <ScheduleIcon />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      {/* Welcome Section */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 1, fontWeight: 600 }}>
          Welcome back, {user?.full_name || user?.email}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here's what's happening with your trading strategies today
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Statistics Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <DocumentIcon />
                </Avatar>
                <Typography variant="h4" sx={{ fontWeight: 600 }}>
                  {stats.totalDocuments}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Documents Processed
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <StrategyIcon />
                </Avatar>
                <Typography variant="h4" sx={{ fontWeight: 600 }}>
                  {stats.totalStrategies}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Strategies Extracted
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <BacktestIcon />
                </Avatar>
                <Typography variant="h4" sx={{ fontWeight: 600 }}>
                  {stats.totalBacktests}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Backtests Run
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>
                    %
                  </Typography>
                </Avatar>
                <Typography variant="h4" sx={{ fontWeight: 600 }}>
                  {stats.successRate}%
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Success Rate
              </Typography>
              <LinearProgress
                variant="determinate"
                value={stats.successRate}
                sx={{ mt: 1, height: 4, borderRadius: 2 }}
                color="success"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
              Quick Actions
            </Typography>
            <Grid container spacing={2}>
              {quickActions.map((action, index) => (
                <Grid item xs={12} sm={4} key={index}>
                  <Card 
                    sx={{ 
                      cursor: 'pointer', 
                      height: '100%',
                      '&:hover': { 
                        boxShadow: 3,
                        transform: 'translateY(-2px)',
                        transition: 'all 0.2s ease-in-out'
                      }
                    }}
                    onClick={action.action}
                  >
                    <CardContent sx={{ textAlign: 'center', p: 3 }}>
                      <Avatar 
                        sx={{ 
                          bgcolor: `${action.color}.main`, 
                          mx: 'auto', 
                          mb: 2,
                          width: 48,
                          height: 48
                        }}
                      >
                        {action.icon}
                      </Avatar>
                      <Typography variant="h6" sx={{ mb: 1, fontWeight: 600 }}>
                        {action.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {action.description}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
              Recent Activity
            </Typography>
            <List>
              {recentActivity.map((activity, index) => (
                <React.Fragment key={activity.id}>
                  <ListItem sx={{ px: 0 }}>
                    <ListItemAvatar>
                      {getStatusIcon(activity.status)}
                    </ListItemAvatar>
                    <ListItemText
                      primary={activity.title}
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <Chip
                            label={activity.status}
                            size="small"
                            color={getStatusColor(activity.status) as any}
                            variant="outlined"
                          />
                          <Typography variant="caption" color="text.secondary">
                            {activity.time}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                  {index < recentActivity.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
            <Button
              fullWidth
              variant="outlined"
              sx={{ mt: 2 }}
              onClick={() => navigate('/notifications')}
            >
              View All Activity
            </Button>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;