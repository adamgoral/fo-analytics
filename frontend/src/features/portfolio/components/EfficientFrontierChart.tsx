import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  Chip,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Slider,
} from '@mui/material';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Line,
  ComposedChart,
  ReferenceDot,
} from 'recharts';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { TrendingUp, Add } from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../../store';
import { calculateEfficientFrontier } from '../../../store/portfolioSlice';

const EfficientFrontierChart: React.FC = () => {
  const dispatch = useAppDispatch();
  const { efficientFrontier } = useAppSelector((state) => state.portfolio);

  const [symbols, setSymbols] = useState<string[]>(['AAPL', 'GOOGL', 'MSFT', 'AMZN']);
  const [newSymbol, setNewSymbol] = useState('');
  const [startDate, setStartDate] = useState<Date | null>(
    new Date(new Date().setFullYear(new Date().getFullYear() - 2))
  );
  const [endDate, setEndDate] = useState<Date | null>(new Date());
  const [riskFreeRate, setRiskFreeRate] = useState<number>(0.02);
  const [numPortfolios, setNumPortfolios] = useState<number>(50);
  const [selectedPortfolioIndex, setSelectedPortfolioIndex] = useState<number | null>(null);

  const handleAddSymbol = () => {
    if (newSymbol && !symbols.includes(newSymbol.toUpperCase())) {
      setSymbols([...symbols, newSymbol.toUpperCase()]);
      setNewSymbol('');
    }
  };

  const handleRemoveSymbol = (symbol: string) => {
    setSymbols(symbols.filter((s) => s !== symbol));
  };

  const handleCalculate = () => {
    if (symbols.length < 2) {
      return;
    }

    const request = {
      symbols,
      start_date: startDate?.toISOString().split('T')[0] || '',
      end_date: endDate?.toISOString().split('T')[0] || '',
      risk_free_rate: riskFreeRate,
      n_portfolios: numPortfolios,
    };

    dispatch(calculateEfficientFrontier(request));
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(2)}%`;

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const portfolioIndex = efficientFrontier?.data?.portfolios.findIndex(
        p => p.volatility === data.volatility && p.expected_return === data.expected_return
      );

      return (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Portfolio {portfolioIndex !== undefined ? portfolioIndex + 1 : ''}
          </Typography>
          <Typography variant="body2">
            Expected Return: {formatPercent(data.expected_return)}
          </Typography>
          <Typography variant="body2">
            Volatility: {formatPercent(data.volatility)}
          </Typography>
          <Typography variant="body2">
            Sharpe Ratio: {data.sharpe_ratio.toFixed(3)}
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  const chartData = efficientFrontier?.data?.portfolios.map((portfolio, index) => ({
    ...portfolio,
    volatility: portfolio.volatility * 100,
    expected_return: portfolio.expected_return * 100,
    index,
  }));

  const selectedPortfolio = selectedPortfolioIndex !== null && efficientFrontier?.data?.portfolios[selectedPortfolioIndex];

  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Configuration
            </Typography>

            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={12}>
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
                <Grid item xs={12}>
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

            <TextField
              fullWidth
              label="Risk-Free Rate"
              type="number"
              value={riskFreeRate}
              onChange={(e) => setRiskFreeRate(parseFloat(e.target.value))}
              InputProps={{
                endAdornment: '%',
              }}
              sx={{ mb: 2 }}
            />

            <FormControl fullWidth sx={{ mb: 3 }}>
              <Typography gutterBottom>
                Number of Portfolios: {numPortfolios}
              </Typography>
              <Slider
                value={numPortfolios}
                onChange={(e, value) => setNumPortfolios(value as number)}
                min={20}
                max={100}
                step={10}
                marks
                valueLabelDisplay="auto"
              />
            </FormControl>

            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle1" gutterBottom>
                Assets
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

              {symbols.length < 2 && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  Add at least 2 assets to calculate efficient frontier
                </Alert>
              )}
            </Box>

            <Button
              fullWidth
              variant="contained"
              onClick={handleCalculate}
              disabled={symbols.length < 2 || efficientFrontier.loading}
              startIcon={
                efficientFrontier.loading ? <CircularProgress size={20} /> : <TrendingUp />
              }
            >
              {efficientFrontier.loading ? 'Calculating...' : 'Calculate Frontier'}
            </Button>

            {efficientFrontier.error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {efficientFrontier.error}
              </Alert>
            )}
          </Paper>

          {selectedPortfolio && (
            <Paper sx={{ p: 3, mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Selected Portfolio
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Expected Return
                </Typography>
                <Typography variant="h6" color="primary">
                  {formatPercent(selectedPortfolio.expected_return)}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Volatility
                </Typography>
                <Typography variant="h6" color="warning.main">
                  {formatPercent(selectedPortfolio.volatility)}
                </Typography>
              </Box>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Sharpe Ratio
                </Typography>
                <Typography variant="h6" color="success.main">
                  {selectedPortfolio.sharpe_ratio.toFixed(3)}
                </Typography>
              </Box>

              <Typography variant="subtitle2" gutterBottom sx={{ mt: 3 }}>
                Weights
              </Typography>
              {Object.entries(selectedPortfolio.weights).map(([symbol, weight]) => (
                <Box key={symbol} sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">{symbol}</Typography>
                  <Typography variant="body2" color="primary">
                    {formatPercent(weight)}
                  </Typography>
                </Box>
              ))}
            </Paper>
          )}
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: 600 }}>
            <Typography variant="h6" gutterBottom>
              Efficient Frontier
            </Typography>

            {chartData && chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="90%">
                <ScatterChart
                  margin={{ top: 20, right: 20, bottom: 60, left: 60 }}
                  onClick={(e) => {
                    if (e && e.activePayload && e.activePayload[0]) {
                      setSelectedPortfolioIndex(e.activePayload[0].payload.index);
                    }
                  }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    type="number"
                    dataKey="volatility"
                    name="Volatility"
                    unit="%"
                    label={{ value: 'Volatility (%)', position: 'insideBottom', offset: -10 }}
                  />
                  <YAxis
                    type="number"
                    dataKey="expected_return"
                    name="Expected Return"
                    unit="%"
                    label={{ value: 'Expected Return (%)', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Scatter
                    name="Portfolios"
                    data={chartData}
                    fill="#8884d8"
                    cursor="pointer"
                  />
                  {selectedPortfolioIndex !== null && (
                    <ReferenceDot
                      x={chartData[selectedPortfolioIndex].volatility}
                      y={chartData[selectedPortfolioIndex].expected_return}
                      r={8}
                      fill="#ff7300"
                      stroke="none"
                    />
                  )}
                </ScatterChart>
              </ResponsiveContainer>
            ) : (
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '90%' }}>
                <Typography variant="body1" color="textSecondary">
                  Configure settings and click "Calculate Frontier" to visualize the efficient frontier
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default EfficientFrontierChart;