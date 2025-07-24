import React, { useEffect, useState } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Tabs,
  Tab,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  TrendingUp,
  ShowChart,
  PieChart,
  Assessment,
  Refresh,
  Download,
} from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../store';
import {
  setSelectedTab,
  fetchOptimizationMethods,
  setCurrentPortfolio,
} from '../../store/portfolioSlice';
import PortfolioOverview from './components/PortfolioOverview';
import PortfolioOptimizer from './components/PortfolioOptimizer';
import EfficientFrontierChart from './components/EfficientFrontierChart';
import RiskAnalysis from './components/RiskAnalysis';
import MultiStrategyAnalyzer from './components/MultiStrategyAnalyzer';
import AllocationChart from './components/AllocationChart';
import { mockPortfolioData } from './mockData';

// Development mode flag - set to true to use mock data
const USE_MOCK_DATA = true;

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`portfolio-tabpanel-${index}`}
      aria-labelledby={`portfolio-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const PortfolioPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const { selectedTab, currentPortfolio, optimizationMethods } = useAppSelector(
    (state) => state.portfolio
  );
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    // Fetch optimization methods on mount
    dispatch(fetchOptimizationMethods());
    
    // Load mock data in development mode
    if (USE_MOCK_DATA && !currentPortfolio) {
      dispatch(setCurrentPortfolio(mockPortfolioData));
    }
  }, [dispatch, currentPortfolio]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    dispatch(setSelectedTab(newValue));
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    // Refresh portfolio data
    await dispatch(fetchOptimizationMethods());
    setRefreshing(false);
  };

  const handleExport = () => {
    // Export portfolio data
    if (currentPortfolio) {
      const dataStr = JSON.stringify(currentPortfolio, null, 2);
      const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
      const exportFileDefaultName = `portfolio_${new Date().toISOString()}.json`;
      
      const linkElement = document.createElement('a');
      linkElement.setAttribute('href', dataUri);
      linkElement.setAttribute('download', exportFileDefaultName);
      linkElement.click();
    }
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" component="h1">
            Portfolio Analytics Dashboard
          </Typography>
          <Box>
            <Tooltip title="Refresh data">
              <IconButton onClick={handleRefresh} disabled={refreshing}>
                {refreshing ? <CircularProgress size={24} /> : <Refresh />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Export portfolio data">
              <IconButton onClick={handleExport} disabled={!currentPortfolio}>
                <Download />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Key Metrics Summary */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <TrendingUp color="primary" sx={{ mr: 1 }} />
                  <Typography color="textSecondary" gutterBottom>
                    Total Portfolio Value
                  </Typography>
                </Box>
                <Typography variant="h5" component="div">
                  ${currentPortfolio?.total_value?.toLocaleString() || '0'}
                </Typography>
                <Typography variant="body2" color={currentPortfolio?.total_pnl_percent && currentPortfolio.total_pnl_percent >= 0 ? 'success.main' : 'error.main'}>
                  {currentPortfolio?.total_pnl_percent?.toFixed(2) || '0'}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <ShowChart color="primary" sx={{ mr: 1 }} />
                  <Typography color="textSecondary" gutterBottom>
                    Total P&L
                  </Typography>
                </Box>
                <Typography variant="h5" component="div">
                  ${currentPortfolio?.total_pnl?.toLocaleString() || '0'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Unrealized gains/losses
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <PieChart color="primary" sx={{ mr: 1 }} />
                  <Typography color="textSecondary" gutterBottom>
                    Asset Classes
                  </Typography>
                </Box>
                <Typography variant="h5" component="div">
                  {Object.keys(currentPortfolio?.allocation_by_asset_class || {}).length}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Diversified portfolio
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Assessment color="primary" sx={{ mr: 1 }} />
                  <Typography color="textSecondary" gutterBottom>
                    Positions
                  </Typography>
                </Box>
                <Typography variant="h5" component="div">
                  {currentPortfolio?.positions?.length || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Active holdings
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Main Content Tabs */}
        <Paper sx={{ width: '100%' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs
              value={selectedTab}
              onChange={handleTabChange}
              aria-label="portfolio analytics tabs"
              variant="scrollable"
              scrollButtons="auto"
            >
              <Tab label="Overview" />
              <Tab label="Optimization" />
              <Tab label="Efficient Frontier" />
              <Tab label="Risk Analysis" />
              <Tab label="Multi-Strategy" />
            </Tabs>
          </Box>

          <TabPanel value={selectedTab} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <PortfolioOverview />
              </Grid>
              <Grid item xs={12} md={4}>
                <AllocationChart />
              </Grid>
            </Grid>
          </TabPanel>

          <TabPanel value={selectedTab} index={1}>
            <PortfolioOptimizer />
          </TabPanel>

          <TabPanel value={selectedTab} index={2}>
            <EfficientFrontierChart />
          </TabPanel>

          <TabPanel value={selectedTab} index={3}>
            <RiskAnalysis />
          </TabPanel>

          <TabPanel value={selectedTab} index={4}>
            <MultiStrategyAnalyzer />
          </TabPanel>
        </Paper>
      </Box>
    </Container>
  );
};

export default PortfolioPage;