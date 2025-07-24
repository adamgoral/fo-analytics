import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Alert,
  Button,
  IconButton,
  Tooltip,
  Grid,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Download as DownloadIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { backtestsApi } from '../../services/backtests';
import type { BacktestResult } from '../../services/backtests';


interface BacktestResultsProps {
  backtestId: string;
}

const BacktestResults: React.FC<BacktestResultsProps> = ({ backtestId }) => {
  const [backtest, setBacktest] = useState<BacktestResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAllTrades, setShowAllTrades] = useState(false);

  useEffect(() => {
    loadBacktestResults();
  }, [backtestId]);

  const loadBacktestResults = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await backtestsApi.get(backtestId);
      setBacktest(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load backtest results');
    } finally {
      setLoading(false);
    }
  };

  const formatPercent = (value: number, decimals = 2): string => {
    return `${(value * 100).toFixed(decimals)}%`;
  };

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value: number, decimals = 2): string => {
    return value.toFixed(decimals);
  };

  const getMetricColor = (value: number, metric: string): string => {
    if (metric === 'max_drawdown') {
      return value > -0.1 ? 'success' : value > -0.2 ? 'warning' : 'error';
    }
    return value > 0 ? 'success' : 'error';
  };

  const exportResults = async () => {
    try {
      await backtestsApi.exportResults(backtestId);
    } catch (err: any) {
      console.error('Export failed:', err);
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
          Loading backtest results...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button onClick={loadBacktestResults} startIcon={<RefreshIcon />}>
          Retry
        </Button>
      </Box>
    );
  }

  if (!backtest) {
    return (
      <Alert severity="warning">No backtest data available</Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h5" sx={{ fontWeight: 600 }}>
              Backtest Results
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {backtest.strategy_name} • {backtest.parameters.symbol}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Export Results">
              <IconButton onClick={exportResults} disabled={!backtest.results}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Status and Parameters */}
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Chip
            label={backtest.status}
            color={backtest.status === 'completed' ? 'success' : backtest.status === 'failed' ? 'error' : 'warning'}
            size="small"
          />
          <Chip label={`Period: ${backtest.parameters.start_date} to ${backtest.parameters.end_date}`} size="small" />
          <Chip label={`Initial Capital: ${formatCurrency(backtest.parameters.initial_capital)}`} size="small" />
          <Chip label={`Commission: ${formatPercent(backtest.parameters.commission)}`} size="small" />
        </Box>
      </Box>

      {backtest.status === 'failed' && backtest.error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {backtest.error}
        </Alert>
      )}

      {backtest.status === 'running' && (
        <Box sx={{ mb: 3 }}>
          <LinearProgress />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Backtest is currently running...
          </Typography>
        </Box>
      )}

      {backtest.results && (
        <>
          {/* Key Metrics */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Total Return
                      </Typography>
                      <Typography variant="h5" sx={{ fontWeight: 600, color: getMetricColor(backtest.results.total_return, 'return') }}>
                        {formatPercent(backtest.results.total_return)}
                      </Typography>
                    </Box>
                    {backtest.results.total_return > 0 ? <TrendingUpIcon color="success" /> : <TrendingDownIcon color="error" />}
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Sharpe Ratio
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {formatNumber(backtest.results.sharpe_ratio)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Risk-adjusted return
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Max Drawdown
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600, color: getMetricColor(backtest.results.max_drawdown, 'max_drawdown') }}>
                    {formatPercent(backtest.results.max_drawdown)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Largest peak-to-trough decline
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Win Rate
                  </Typography>
                  <Typography variant="h5" sx={{ fontWeight: 600 }}>
                    {formatPercent(backtest.results.win_rate)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {backtest.results.winning_trades} of {backtest.results.total_trades} trades
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Additional Metrics */}
          <Paper variant="outlined" sx={{ p: 3, mb: 4 }}>
            <Typography variant="h6" sx={{ mb: 3, fontWeight: 600 }}>
              Performance Metrics
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6} md={4}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Annualized Return
                  </Typography>
                  <Typography variant="h6">
                    {formatPercent(backtest.results.annualized_return)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Sortino Ratio
                  </Typography>
                  <Typography variant="h6">
                    {formatNumber(backtest.results.sortino_ratio)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Profit Factor
                  </Typography>
                  <Typography variant="h6">
                    {formatNumber(backtest.results.profit_factor)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Average Win
                  </Typography>
                  <Typography variant="h6">
                    {formatPercent(backtest.results.avg_win)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Average Loss
                  </Typography>
                  <Typography variant="h6">
                    {formatPercent(backtest.results.avg_loss)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6} md={4}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Best Trade
                  </Typography>
                  <Typography variant="h6">
                    {formatPercent(backtest.results.best_trade)}
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>

          {/* Trade History */}
          <Paper variant="outlined" sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Trade History
              </Typography>
              <Button
                size="small"
                onClick={() => setShowAllTrades(!showAllTrades)}
              >
                {showAllTrades ? 'Show Recent' : 'Show All'}
              </Button>
            </Box>
            
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Entry Date</TableCell>
                    <TableCell>Exit Date</TableCell>
                    <TableCell align="right">Entry Price</TableCell>
                    <TableCell align="right">Exit Price</TableCell>
                    <TableCell align="right">Size</TableCell>
                    <TableCell align="right">P&L</TableCell>
                    <TableCell align="right">Return</TableCell>
                    <TableCell align="right">Duration</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(showAllTrades ? backtest.results.trades : backtest.results.trades.slice(0, 10)).map((trade, index) => (
                    <TableRow key={index}>
                      <TableCell>{new Date(trade.entry_date).toLocaleDateString()}</TableCell>
                      <TableCell>{new Date(trade.exit_date).toLocaleDateString()}</TableCell>
                      <TableCell align="right">${trade.entry_price.toFixed(2)}</TableCell>
                      <TableCell align="right">${trade.exit_price.toFixed(2)}</TableCell>
                      <TableCell align="right">{trade.size}</TableCell>
                      <TableCell align="right" sx={{ color: trade.pnl > 0 ? 'success.main' : 'error.main' }}>
                        {formatCurrency(trade.pnl)}
                      </TableCell>
                      <TableCell align="right" sx={{ color: trade.return_pct > 0 ? 'success.main' : 'error.main' }}>
                        {formatPercent(trade.return_pct)}
                      </TableCell>
                      <TableCell align="right">{trade.duration_days}d</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            
            {!showAllTrades && backtest.results.trades.length > 10 && (
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2, textAlign: 'center' }}>
                Showing 10 of {backtest.results.trades.length} trades
              </Typography>
            )}
          </Paper>
        </>
      )}
    </Box>
  );
};

export default BacktestResults;