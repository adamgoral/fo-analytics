import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Tooltip,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { Add, Remove, Calculate, Info } from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../../store';
import {
  optimizePortfolio,
  setSelectedOptimizationMethod,
} from '../../../store/portfolioSlice';
import { OptimizationMethod } from '../../../types/portfolio';

const PortfolioOptimizer: React.FC = () => {
  const dispatch = useAppDispatch();
  const {
    optimization,
    selectedOptimizationMethod,
    optimizationMethods,
  } = useAppSelector((state) => state.portfolio);

  const [symbols, setSymbols] = useState<string[]>(['AAPL', 'GOOGL', 'MSFT']);
  const [newSymbol, setNewSymbol] = useState('');
  const [startDate, setStartDate] = useState<Date | null>(
    new Date(new Date().setFullYear(new Date().getFullYear() - 1))
  );
  const [endDate, setEndDate] = useState<Date | null>(new Date());
  const [targetReturn, setTargetReturn] = useState<number>(0.15);
  const [riskFreeRate, setRiskFreeRate] = useState<number>(0.02);

  const handleAddSymbol = () => {
    if (newSymbol && !symbols.includes(newSymbol.toUpperCase())) {
      setSymbols([...symbols, newSymbol.toUpperCase()]);
      setNewSymbol('');
    }
  };

  const handleRemoveSymbol = (symbol: string) => {
    setSymbols(symbols.filter((s) => s !== symbol));
  };

  const handleOptimize = () => {
    if (symbols.length < 2) {
      return;
    }

    const request = {
      symbols,
      start_date: startDate?.toISOString().split('T')[0] || '',
      end_date: endDate?.toISOString().split('T')[0] || '',
      method: selectedOptimizationMethod as OptimizationMethod,
      target_return: targetReturn,
      risk_free_rate: riskFreeRate,
    };

    dispatch(optimizePortfolio(request));
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(2)}%`;

  const renderOptimizationParameters = () => {
    const method = optimizationMethods?.[selectedOptimizationMethod];
    if (!method) return null;

    return (
      <Box sx={{ mt: 2 }}>
        {selectedOptimizationMethod === 'mean_variance' && (
          <TextField
            fullWidth
            label="Target Return"
            type="number"
            value={targetReturn}
            onChange={(e) => setTargetReturn(parseFloat(e.target.value))}
            InputProps={{
              endAdornment: '%',
            }}
            helperText="Annual target return for the portfolio"
          />
        )}
        
        {['max_sharpe', 'mean_variance'].includes(selectedOptimizationMethod) && (
          <TextField
            fullWidth
            label="Risk-Free Rate"
            type="number"
            value={riskFreeRate}
            onChange={(e) => setRiskFreeRate(parseFloat(e.target.value))}
            InputProps={{
              endAdornment: '%',
            }}
            helperText="Risk-free rate for Sharpe ratio calculation"
            sx={{ mt: 2 }}
          />
        )}
      </Box>
    );
  };

  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Optimization Settings
            </Typography>

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Optimization Method</InputLabel>
              <Select
                value={selectedOptimizationMethod}
                onChange={(e) =>
                  dispatch(setSelectedOptimizationMethod(e.target.value))
                }
                label="Optimization Method"
              >
                {optimizationMethods &&
                  Object.entries(optimizationMethods).map(([key, method]) => (
                    <MenuItem key={key} value={key}>
                      <Box>
                        <Typography>{method.name}</Typography>
                        <Typography variant="caption" color="textSecondary">
                          {method.description}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
              </Select>
            </FormControl>

            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <DatePicker
                    label="Start Date"
                    value={startDate}
                    onChange={setStartDate}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                      },
                    }}
                  />
                </Grid>
                <Grid item xs={6}>
                  <DatePicker
                    label="End Date"
                    value={endDate}
                    onChange={setEndDate}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                      },
                    }}
                  />
                </Grid>
              </Grid>
            </LocalizationProvider>

            {renderOptimizationParameters()}

            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Portfolio Assets
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                <TextField
                  size="small"
                  placeholder="Add symbol"
                  value={newSymbol}
                  onChange={(e) => setNewSymbol(e.target.value.toUpperCase())}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      handleAddSymbol();
                    }
                  }}
                />
                <Button
                  variant="contained"
                  onClick={handleAddSymbol}
                  startIcon={<Add />}
                  disabled={!newSymbol}
                >
                  Add
                </Button>
              </Box>

              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {symbols.map((symbol) => (
                  <Chip
                    key={symbol}
                    label={symbol}
                    onDelete={() => handleRemoveSymbol(symbol)}
                    color="primary"
                  />
                ))}
              </Box>

              {symbols.length < 2 && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  Add at least 2 assets to run optimization
                </Alert>
              )}
            </Box>

            <Button
              fullWidth
              variant="contained"
              onClick={handleOptimize}
              disabled={symbols.length < 2 || optimization.loading}
              startIcon={
                optimization.loading ? <CircularProgress size={20} /> : <Calculate />
              }
              sx={{ mt: 3 }}
            >
              {optimization.loading ? 'Optimizing...' : 'Optimize Portfolio'}
            </Button>

            {optimization.error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {optimization.error}
              </Alert>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Optimization Results
            </Typography>

            {optimization.result ? (
              <Box>
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  <Grid item xs={6}>
                    <Paper sx={{ p: 2, backgroundColor: 'action.hover' }}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Expected Return
                      </Typography>
                      <Typography variant="h6" color="primary">
                        {formatPercent(optimization.result.expected_return)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6}>
                    <Paper sx={{ p: 2, backgroundColor: 'action.hover' }}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Volatility
                      </Typography>
                      <Typography variant="h6" color="warning.main">
                        {formatPercent(optimization.result.volatility)}
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={12}>
                    <Paper sx={{ p: 2, backgroundColor: 'action.hover' }}>
                      <Typography variant="subtitle2" color="textSecondary">
                        Sharpe Ratio
                      </Typography>
                      <Typography variant="h6" color="success.main">
                        {optimization.result.sharpe_ratio.toFixed(3)}
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>

                <Typography variant="subtitle1" gutterBottom>
                  Optimal Weights
                </Typography>
                
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Asset</TableCell>
                        <TableCell align="right">Weight</TableCell>
                        <TableCell align="right">Allocation</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(optimization.result.weights)
                        .sort(([, a], [, b]) => b - a)
                        .map(([symbol, weight]) => (
                          <TableRow key={symbol}>
                            <TableCell>
                              <Typography variant="subtitle2">{symbol}</Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Typography>{formatPercent(weight)}</Typography>
                            </TableCell>
                            <TableCell align="right">
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Box
                                  sx={{
                                    width: '100%',
                                    backgroundColor: 'action.hover',
                                    borderRadius: 1,
                                    mr: 1,
                                  }}
                                >
                                  <Box
                                    sx={{
                                      width: `${weight * 100}%`,
                                      backgroundColor: 'primary.main',
                                      height: 20,
                                      borderRadius: 1,
                                    }}
                                  />
                                </Box>
                              </Box>
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                <Button
                  fullWidth
                  variant="outlined"
                  sx={{ mt: 2 }}
                  onClick={() => {
                    // Apply optimization results to current portfolio
                    console.log('Apply optimization results');
                  }}
                >
                  Apply to Portfolio
                </Button>
              </Box>
            ) : (
              <Box sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body1" color="textSecondary">
                  Configure optimization settings and click "Optimize Portfolio" to see results
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PortfolioOptimizer;