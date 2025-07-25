import React, { useState } from 'react';
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
  Slider,
  Chip,
  Alert,
  CircularProgress,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add,
  Remove,
  PlayArrow,
  ExpandMore,
  Settings,
  TrendingUp,
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { useAppDispatch, useAppSelector } from '../../../store';
import { runMultiStrategyBacktest } from '../../../store/portfolioSlice';
import type { RebalanceFrequency, OptimizationMethod } from '../../../types/portfolio';
import EquityChart from '../../../components/Charts/EquityChart';

interface StrategyConfig {
  id: string;
  strategy_type: string;
  parameters: Record<string, any>;
  weight: number;
}

const strategyTypes = [
  { value: 'sma_crossover', label: 'SMA Crossover', params: ['fast_period', 'slow_period'] },
  { value: 'rsi_mean_reversion', label: 'RSI Mean Reversion', params: ['rsi_period', 'oversold', 'overbought'] },
  { value: 'bollinger_bands', label: 'Bollinger Bands', params: ['period', 'std_dev'] },
  { value: 'momentum', label: 'Momentum', params: ['lookback_period'] },
];

const MultiStrategyAnalyzer: React.FC = () => {
  const dispatch = useAppDispatch();
  const { multiStrategyBacktest, optimizationMethods } = useAppSelector(
    (state) => state.portfolio
  );

  const [strategies, setStrategies] = useState<StrategyConfig[]>([
    {
      id: '1',
      strategy_type: 'sma_crossover',
      parameters: { fast_period: 10, slow_period: 30 },
      weight: 0.5,
    },
    {
      id: '2',
      strategy_type: 'rsi_mean_reversion',
      parameters: { rsi_period: 14, oversold: 30, overbought: 70 },
      weight: 0.5,
    },
  ]);

  const [symbols, setSymbols] = useState<string[]>(['SPY', 'QQQ']);
  const [newSymbol, setNewSymbol] = useState('');
  const [startDate, setStartDate] = useState<Date | null>(
    new Date(new Date().setFullYear(new Date().getFullYear() - 3))
  );
  const [endDate, setEndDate] = useState<Date | null>(new Date());
  const [initialCapital, setInitialCapital] = useState(100000);
  const [optimizationMethod, setOptimizationMethod] = useState<OptimizationMethod>('mean_variance');
  const [rebalanceFrequency, setRebalanceFrequency] = useState<RebalanceFrequency>('monthly');

  const handleAddStrategy = () => {
    const newStrategy: StrategyConfig = {
      id: Date.now().toString(),
      strategy_type: 'sma_crossover',
      parameters: { fast_period: 10, slow_period: 30 },
      weight: 0,
    };
    setStrategies([...strategies, newStrategy]);
  };

  const handleRemoveStrategy = (id: string) => {
    setStrategies(strategies.filter((s) => s.id !== id));
  };

  const handleStrategyChange = (id: string, field: string, value: any) => {
    setStrategies(
      strategies.map((s) => {
        if (s.id === id) {
          if (field === 'strategy_type') {
            // Reset parameters when strategy type changes
            const strategyInfo = strategyTypes.find((st) => st.value === value);
            const defaultParams: Record<string, any> = {};
            strategyInfo?.params.forEach((param) => {
              defaultParams[param] = param.includes('period') ? 14 : 50;
            });
            return { ...s, [field]: value, parameters: defaultParams };
          }
          return { ...s, [field]: value };
        }
        return s;
      })
    );
  };

  const handleParameterChange = (id: string, param: string, value: any) => {
    setStrategies(
      strategies.map((s) => {
        if (s.id === id) {
          return {
            ...s,
            parameters: { ...s.parameters, [param]: value },
          };
        }
        return s;
      })
    );
  };

  const handleWeightChange = (id: string, value: number) => {
    const otherStrategies = strategies.filter((s) => s.id !== id);
    const otherWeights = otherStrategies.reduce((sum, s) => sum + s.weight, 0);
    const maxWeight = 1 - otherWeights;
    
    setStrategies(
      strategies.map((s) => {
        if (s.id === id) {
          return { ...s, weight: Math.min(value, maxWeight) };
        }
        return s;
      })
    );
  };

  const normalizeWeights = () => {
    const totalWeight = strategies.reduce((sum, s) => sum + s.weight, 0);
    if (totalWeight === 0) return;
    
    setStrategies(
      strategies.map((s) => ({
        ...s,
        weight: s.weight / totalWeight,
      }))
    );
  };

  const handleAddSymbol = () => {
    if (newSymbol && !symbols.includes(newSymbol.toUpperCase())) {
      setSymbols([...symbols, newSymbol.toUpperCase()]);
      setNewSymbol('');
    }
  };

  const handleRemoveSymbol = (symbol: string) => {
    setSymbols(symbols.filter((s) => s !== symbol));
  };

  const handleRunBacktest = () => {
    const totalWeight = strategies.reduce((sum, s) => sum + s.weight, 0);
    if (Math.abs(totalWeight - 1) > 0.001) {
      normalizeWeights();
      return;
    }

    const request = {
      strategies: strategies.map(({ id, ...rest }) => rest),
      symbols,
      start_date: startDate?.toISOString().split('T')[0] || '',
      end_date: endDate?.toISOString().split('T')[0] || '',
      initial_capital: initialCapital,
      optimization_method: optimizationMethod,
      rebalance_frequency: rebalanceFrequency,
    };

    dispatch(runMultiStrategyBacktest(request));
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(2)}%`;
  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;

  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Strategy Configuration
            </Typography>

            {strategies.map((strategy, index) => (
              <Accordion key={strategy.id} defaultExpanded={index === 0}>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                    <Typography sx={{ flexGrow: 1 }}>
                      {strategyTypes.find((st) => st.value === strategy.strategy_type)?.label}
                    </Typography>
                    <Chip
                      label={`${formatPercent(strategy.weight)}`}
                      color="primary"
                      size="small"
                      sx={{ mr: 1 }}
                    />
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveStrategy(strategy.id);
                      }}
                      disabled={strategies.length <= 1}
                    >
                      <Remove />
                    </IconButton>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Strategy Type</InputLabel>
                        <Select
                          value={strategy.strategy_type}
                          onChange={(e) =>
                            handleStrategyChange(strategy.id, 'strategy_type', e.target.value)
                          }
                          label="Strategy Type"
                        >
                          {strategyTypes.map((type) => (
                            <MenuItem key={type.value} value={type.value}>
                              {type.label}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>

                    {strategyTypes
                      .find((st) => st.value === strategy.strategy_type)
                      ?.params.map((param) => (
                        <Grid item xs={6} key={param}>
                          <TextField
                            fullWidth
                            size="small"
                            label={param.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                            type="number"
                            value={strategy.parameters[param] || ''}
                            onChange={(e) =>
                              handleParameterChange(
                                strategy.id,
                                param,
                                parseFloat(e.target.value)
                              )
                            }
                          />
                        </Grid>
                      ))}

                    <Grid item xs={12}>
                      <Typography gutterBottom>
                        Weight: {formatPercent(strategy.weight)}
                      </Typography>
                      <Slider
                        value={strategy.weight}
                        onChange={(e, value) => handleWeightChange(strategy.id, value as number)}
                        min={0}
                        max={1}
                        step={0.05}
                        marks
                        valueLabelDisplay="auto"
                        valueLabelFormat={formatPercent}
                      />
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))}

            <Button
              fullWidth
              variant="outlined"
              onClick={handleAddStrategy}
              startIcon={<Add />}
              sx={{ mt: 2 }}
            >
              Add Strategy
            </Button>

            {Math.abs(strategies.reduce((sum, s) => sum + s.weight, 0) - 1) > 0.001 && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                Strategy weights must sum to 100%. Click "Normalize Weights" or adjust manually.
                <Button size="small" onClick={normalizeWeights} sx={{ mt: 1 }}>
                  Normalize Weights
                </Button>
              </Alert>
            )}
          </Paper>

          <Paper sx={{ p: 3, mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Portfolio Settings
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Assets
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
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
                      size="small"
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
                        size="small"
                      />
                    ))}
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Optimization Method</InputLabel>
                  <Select
                    value={optimizationMethod}
                    onChange={(e) => setOptimizationMethod(e.target.value as OptimizationMethod)}
                    label="Optimization Method"
                  >
                    {optimizationMethods &&
                      Object.entries(optimizationMethods).map(([key, method]) => (
                        <MenuItem key={key} value={key}>
                          {method.name}
                        </MenuItem>
                      ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={6}>
                <FormControl fullWidth size="small">
                  <InputLabel>Rebalance Frequency</InputLabel>
                  <Select
                    value={rebalanceFrequency}
                    onChange={(e) => setRebalanceFrequency(e.target.value as RebalanceFrequency)}
                    label="Rebalance Frequency"
                  >
                    <MenuItem value="daily">Daily</MenuItem>
                    <MenuItem value="weekly">Weekly</MenuItem>
                    <MenuItem value="monthly">Monthly</MenuItem>
                    <MenuItem value="quarterly">Quarterly</MenuItem>
                    <MenuItem value="yearly">Yearly</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <LocalizationProvider dateAdapter={AdapterDateFns}>
                <Grid item xs={6}>
                  <DatePicker
                    label="Start Date"
                    value={startDate}
                    onChange={setStartDate}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        size: 'small',
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
                        size: 'small',
                      },
                    }}
                  />
                </Grid>
              </LocalizationProvider>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  size="small"
                  label="Initial Capital"
                  type="number"
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(parseInt(e.target.value))}
                  InputProps={{
                    startAdornment: '$',
                  }}
                />
              </Grid>
            </Grid>

            <Button
              fullWidth
              variant="contained"
              onClick={handleRunBacktest}
              disabled={
                strategies.length === 0 ||
                symbols.length === 0 ||
                multiStrategyBacktest.loading
              }
              startIcon={
                multiStrategyBacktest.loading ? <CircularProgress size={20} /> : <PlayArrow />
              }
              sx={{ mt: 3 }}
            >
              {multiStrategyBacktest.loading ? 'Running Backtest...' : 'Run Multi-Strategy Backtest'}
            </Button>

            {multiStrategyBacktest.error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {multiStrategyBacktest.error}
              </Alert>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={5}>
          {multiStrategyBacktest.result ? (
            <Box>
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Performance Summary
                </Typography>

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom>
                          Total Return
                        </Typography>
                        <Typography
                          variant="h5"
                          color={multiStrategyBacktest.result.total_return >= 0 ? 'success.main' : 'error.main'}
                        >
                          {formatPercent(multiStrategyBacktest.result.total_return)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom>
                          Annual Return
                        </Typography>
                        <Typography variant="h5" color="primary">
                          {formatPercent(multiStrategyBacktest.result.annual_return)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom>
                          Sharpe Ratio
                        </Typography>
                        <Typography variant="h5">
                          {multiStrategyBacktest.result.sharpe_ratio.toFixed(2)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={6}>
                    <Card>
                      <CardContent>
                        <Typography color="textSecondary" gutterBottom>
                          Max Drawdown
                        </Typography>
                        <Typography variant="h5" color="error">
                          {formatPercent(multiStrategyBacktest.result.max_drawdown)}
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>
              </Paper>

              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Strategy Weights
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Strategy</TableCell>
                        <TableCell align="right">Weight</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {Object.entries(multiStrategyBacktest.result.strategy_weights).map(
                        ([strategy, weight]) => (
                          <TableRow key={strategy}>
                            <TableCell>{strategy}</TableCell>
                            <TableCell align="right">{formatPercent(weight)}</TableCell>
                          </TableRow>
                        )
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>

              <Paper sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Equity Curve
                </Typography>
                <Box sx={{ height: 300 }}>
                  <EquityChart
                    data={multiStrategyBacktest.result.equity_curve.map((point) => ({
                      date: point.timestamp,
                      value: point.value,
                    }))}
                    height={280}
                  />
                </Box>
              </Paper>
            </Box>
          ) : (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <Settings sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="textSecondary" gutterBottom>
                Configure Your Multi-Strategy Portfolio
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Add strategies, set parameters, and run a backtest to see results
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default MultiStrategyAnalyzer;