import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  Warning,
  TrendingDown,
  Speed,
  BarChart,
  Info,
  Refresh,
} from '@mui/icons-material';
import { useAppSelector } from '../../../store';
import type { RiskMetricsResponse } from '../../../types/portfolio';

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
      id={`risk-tabpanel-${index}`}
      aria-labelledby={`risk-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const RiskAnalysis: React.FC = () => {
  const { riskMetrics, currentPortfolio } = useAppSelector((state) => state.portfolio);
  const [selectedTab, setSelectedTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(2)}%`;
  const formatNumber = (value: number) => value.toFixed(3);

  const getRiskLevel = (value: number, metric: string): 'low' | 'medium' | 'high' => {
    switch (metric) {
      case 'var':
        return value > -0.05 ? 'low' : value > -0.1 ? 'medium' : 'high';
      case 'drawdown':
        return value > -0.1 ? 'low' : value > -0.2 ? 'medium' : 'high';
      case 'volatility':
        return value < 0.15 ? 'low' : value < 0.25 ? 'medium' : 'high';
      default:
        return 'medium';
    }
  };

  const getRiskColor = (level: 'low' | 'medium' | 'high') => {
    switch (level) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
    }
  };

  if (!riskMetrics.data) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h6" color="textSecondary" gutterBottom>
          No risk analysis data available
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Run portfolio optimization or load historical data to see risk metrics
        </Typography>
      </Paper>
    );
  }

  const metrics = riskMetrics.data;

  return (
    <Box>
      {/* Risk Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Warning color="error" sx={{ mr: 1 }} />
                <Typography color="textSecondary" variant="subtitle2">
                  Value at Risk (95%)
                </Typography>
              </Box>
              <Typography variant="h5" component="div">
                {formatPercent(metrics.var_metrics.historical_var)}
              </Typography>
              <Chip
                label={getRiskLevel(metrics.var_metrics.historical_var, 'var').toUpperCase()}
                color={getRiskColor(getRiskLevel(metrics.var_metrics.historical_var, 'var'))}
                size="small"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingDown color="error" sx={{ mr: 1 }} />
                <Typography color="textSecondary" variant="subtitle2">
                  Max Drawdown
                </Typography>
              </Box>
              <Typography variant="h5" component="div">
                {formatPercent(metrics.drawdown_metrics.max_drawdown)}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Duration: {metrics.drawdown_metrics.max_drawdown_duration} days
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Speed color="primary" sx={{ mr: 1 }} />
                <Typography color="textSecondary" variant="subtitle2">
                  Sharpe Ratio
                </Typography>
              </Box>
              <Typography variant="h5" component="div">
                {formatNumber(metrics.performance_ratios.sharpe_ratio)}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min(100, (metrics.performance_ratios.sharpe_ratio / 3) * 100)}
                sx={{ mt: 1 }}
                color={metrics.performance_ratios.sharpe_ratio > 1 ? 'success' : 'warning'}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <BarChart color="primary" sx={{ mr: 1 }} />
                <Typography color="textSecondary" variant="subtitle2">
                  Volatility
                </Typography>
              </Box>
              <Typography variant="h5" component="div">
                {formatPercent(metrics.basic_stats.std)}
              </Typography>
              <Chip
                label={getRiskLevel(metrics.basic_stats.std, 'volatility').toUpperCase()}
                color={getRiskColor(getRiskLevel(metrics.basic_stats.std, 'volatility'))}
                size="small"
                sx={{ mt: 1 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Detailed Risk Metrics */}
      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={selectedTab} onChange={handleTabChange} aria-label="risk analysis tabs">
            <Tab label="VaR Analysis" />
            <Tab label="Drawdown Analysis" />
            <Tab label="Performance Ratios" />
            <Tab label="Statistical Measures" />
            {metrics.relative_metrics && <Tab label="Relative Metrics" />}
          </Tabs>
        </Box>

        <TabPanel value={selectedTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Value at Risk (VaR) Metrics
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Historical VaR</TableCell>
                      <TableCell align="right">
                        <Typography color="error">
                          {formatPercent(metrics.var_metrics.historical_var)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Parametric VaR</TableCell>
                      <TableCell align="right">
                        <Typography color="error">
                          {formatPercent(metrics.var_metrics.parametric_var)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Cornish-Fisher VaR</TableCell>
                      <TableCell align="right">
                        <Typography color="error">
                          {formatPercent(metrics.var_metrics.cornish_fisher_var)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Monte Carlo VaR</TableCell>
                      <TableCell align="right">
                        <Typography color="error">
                          {formatPercent(metrics.var_metrics.monte_carlo_var)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          Conditional VaR (CVaR)
                          <Tooltip title="Expected loss beyond VaR threshold">
                            <IconButton size="small">
                              <Info fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Typography color="error" sx={{ fontWeight: 'bold' }}>
                          {formatPercent(metrics.var_metrics.cvar)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>

            <Grid item xs={12} md={6}>
              <Alert severity="info">
                <Typography variant="subtitle2" gutterBottom>
                  Understanding VaR
                </Typography>
                <Typography variant="body2">
                  VaR represents the maximum loss expected (with a given confidence level) over a specific time period.
                  A -5% VaR means there's a 5% chance of losing more than 5% in the given period.
                </Typography>
              </Alert>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={selectedTab} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Drawdown Metrics
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Maximum Drawdown</TableCell>
                      <TableCell align="right">
                        <Typography color="error" sx={{ fontWeight: 'bold' }}>
                          {formatPercent(metrics.drawdown_metrics.max_drawdown)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Max Drawdown Duration</TableCell>
                      <TableCell align="right">
                        {metrics.drawdown_metrics.max_drawdown_duration} days
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Average Drawdown</TableCell>
                      <TableCell align="right">
                        <Typography color="warning.main">
                          {formatPercent(metrics.drawdown_metrics.average_drawdown)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Recovery Time</TableCell>
                      <TableCell align="right">
                        {metrics.drawdown_metrics.recovery_time} days
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2, backgroundColor: 'action.hover' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Drawdown Risk Assessment
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Risk Level
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={Math.abs(metrics.drawdown_metrics.max_drawdown) * 200}
                    color={getRiskColor(getRiskLevel(metrics.drawdown_metrics.max_drawdown, 'drawdown'))}
                    sx={{ height: 10, borderRadius: 1 }}
                  />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
                    <Typography variant="caption">Low Risk</Typography>
                    <Typography variant="caption">High Risk</Typography>
                  </Box>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={selectedTab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Performance Ratios
              </Typography>
              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Metric</TableCell>
                      <TableCell align="right">Value</TableCell>
                      <TableCell>Description</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell>
                        <Typography variant="subtitle2">Sharpe Ratio</Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography color="primary" sx={{ fontWeight: 'bold' }}>
                          {formatNumber(metrics.performance_ratios.sharpe_ratio)}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="textSecondary">
                          Risk-adjusted returns (higher is better)
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <Typography variant="subtitle2">Sortino Ratio</Typography>
                      </TableCell>
                      <TableCell align="right">
                        {formatNumber(metrics.performance_ratios.sortino_ratio)}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="textSecondary">
                          Downside risk-adjusted returns
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <Typography variant="subtitle2">Calmar Ratio</Typography>
                      </TableCell>
                      <TableCell align="right">
                        {formatNumber(metrics.performance_ratios.calmar_ratio)}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="textSecondary">
                          Return vs max drawdown
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <Typography variant="subtitle2">Omega Ratio</Typography>
                      </TableCell>
                      <TableCell align="right">
                        {formatNumber(metrics.performance_ratios.omega_ratio)}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="textSecondary">
                          Probability of gains vs losses
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <Typography variant="subtitle2">Gain/Loss Ratio</Typography>
                      </TableCell>
                      <TableCell align="right">
                        {formatNumber(metrics.performance_ratios.gain_loss_ratio)}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="textSecondary">
                          Average gain vs average loss
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <Typography variant="subtitle2">Profit Factor</Typography>
                      </TableCell>
                      <TableCell align="right">
                        {formatNumber(metrics.performance_ratios.profit_factor)}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="textSecondary">
                          Gross profit vs gross loss
                        </Typography>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <Typography variant="subtitle2">Tail Ratio</Typography>
                      </TableCell>
                      <TableCell align="right">
                        {formatNumber(metrics.performance_ratios.tail_ratio)}
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="textSecondary">
                          Right tail vs left tail
                        </Typography>
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={selectedTab} index={3}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Statistical Measures
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>Mean Return</TableCell>
                      <TableCell align="right">
                        {formatPercent(metrics.basic_stats.mean)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Standard Deviation</TableCell>
                      <TableCell align="right">
                        {formatPercent(metrics.basic_stats.std)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          Skewness
                          <Tooltip title="Negative skew indicates more frequent small gains and occasional large losses">
                            <IconButton size="small">
                              <Info fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        {formatNumber(metrics.basic_stats.skewness)}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          Kurtosis
                          <Tooltip title="Higher kurtosis indicates more extreme returns (fat tails)">
                            <IconButton size="small">
                              <Info fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        {formatNumber(metrics.basic_stats.kurtosis)}
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>

            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2, backgroundColor: 'action.hover' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Distribution Analysis
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="textSecondary">
                    Skewness: {metrics.basic_stats.skewness < 0 ? 'Negative' : 'Positive'}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {metrics.basic_stats.skewness < 0
                      ? 'More frequent small gains, occasional large losses'
                      : 'More frequent small losses, occasional large gains'}
                  </Typography>
                  
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                    Kurtosis: {metrics.basic_stats.kurtosis > 3 ? 'High' : 'Normal'}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {metrics.basic_stats.kurtosis > 3
                      ? 'Fat tails - higher probability of extreme returns'
                      : 'Normal distribution of returns'}
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          </Grid>
        </TabPanel>

        {metrics.relative_metrics && (
          <TabPanel value={selectedTab} index={4}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom>
                  Benchmark Relative Metrics
                </Typography>
                <TableContainer component={Paper}>
                  <Table>
                    <TableBody>
                      <TableRow>
                        <TableCell>
                          <Typography variant="subtitle2">Information Ratio</Typography>
                        </TableCell>
                        <TableCell align="right">
                          {formatNumber(metrics.relative_metrics.information_ratio)}
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="textSecondary">
                            Active return per unit of tracking risk
                          </Typography>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>
                          <Typography variant="subtitle2">Beta</Typography>
                        </TableCell>
                        <TableCell align="right">
                          {formatNumber(metrics.relative_metrics.beta)}
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="textSecondary">
                            Sensitivity to market movements
                          </Typography>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>
                          <Typography variant="subtitle2">Alpha</Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography
                            color={metrics.relative_metrics.alpha > 0 ? 'success.main' : 'error.main'}
                          >
                            {formatPercent(metrics.relative_metrics.alpha)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="textSecondary">
                            Excess return vs benchmark
                          </Typography>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>
                          <Typography variant="subtitle2">Correlation</Typography>
                        </TableCell>
                        <TableCell align="right">
                          {formatNumber(metrics.relative_metrics.correlation)}
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="textSecondary">
                            Correlation with benchmark
                          </Typography>
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>
                          <Typography variant="subtitle2">R-Squared</Typography>
                        </TableCell>
                        <TableCell align="right">
                          {formatPercent(metrics.relative_metrics.r_squared)}
                        </TableCell>
                        <TableCell>
                          <Typography variant="caption" color="textSecondary">
                            Percentage of variance explained by benchmark
                          </Typography>
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            </Grid>
          </TabPanel>
        )}
      </Paper>
    </Box>
  );
};

export default RiskAnalysis;