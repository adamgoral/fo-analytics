import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
} from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';
import { useAppSelector } from '../../../store';
import type { PortfolioPosition } from '../../../types/portfolio';

const PortfolioOverview: React.FC = () => {
  const { currentPortfolio } = useAppSelector((state) => state.portfolio);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const getPerformanceColor = (value: number) => {
    return value >= 0 ? 'success' : 'error';
  };

  const renderPosition = (position: PortfolioPosition) => {
    const pnlPercent = ((position.market_value - position.cost_basis) / position.cost_basis) * 100;
    
    return (
      <TableRow key={position.symbol} hover>
        <TableCell>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
              {position.symbol}
            </Typography>
            <Chip
              label={position.asset_class}
              size="small"
              sx={{ ml: 1 }}
              variant="outlined"
            />
          </Box>
        </TableCell>
        <TableCell align="right">{position.quantity.toLocaleString()}</TableCell>
        <TableCell align="right">{formatCurrency(position.current_price)}</TableCell>
        <TableCell align="right">{formatCurrency(position.cost_basis)}</TableCell>
        <TableCell align="right">{formatCurrency(position.market_value)}</TableCell>
        <TableCell align="right">
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
            {position.unrealized_pnl >= 0 ? (
              <TrendingUp color="success" fontSize="small" sx={{ mr: 0.5 }} />
            ) : (
              <TrendingDown color="error" fontSize="small" sx={{ mr: 0.5 }} />
            )}
            <Typography
              variant="body2"
              color={`${getPerformanceColor(position.unrealized_pnl)}.main`}
              sx={{ fontWeight: 'medium' }}
            >
              {formatCurrency(position.unrealized_pnl)}
            </Typography>
          </Box>
          <Typography
            variant="caption"
            color={`${getPerformanceColor(pnlPercent)}.main`}
          >
            ({formatPercent(pnlPercent)})
          </Typography>
        </TableCell>
        <TableCell align="right">
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
            <Box sx={{ width: 60, mr: 1 }}>
              <LinearProgress
                variant="determinate"
                value={position.weight * 100}
                color={position.weight > 0.25 ? 'warning' : 'primary'}
                sx={{ height: 6, borderRadius: 1 }}
              />
            </Box>
            <Typography variant="body2">{formatPercent(position.weight * 100)}</Typography>
          </Box>
        </TableCell>
      </TableRow>
    );
  };

  if (!currentPortfolio || !currentPortfolio.positions?.length) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center' }}>
        <Typography variant="h6" color="textSecondary">
          No portfolio data available
        </Typography>
        <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
          Add positions or run portfolio optimization to see results
        </Typography>
      </Paper>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Portfolio Holdings
      </Typography>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Symbol</TableCell>
              <TableCell align="right">Quantity</TableCell>
              <TableCell align="right">Current Price</TableCell>
              <TableCell align="right">Cost Basis</TableCell>
              <TableCell align="right">Market Value</TableCell>
              <TableCell align="right">Unrealized P&L</TableCell>
              <TableCell align="right">Weight</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {currentPortfolio.positions.map(renderPosition)}
            
            {/* Total Row */}
            <TableRow sx={{ backgroundColor: 'action.hover' }}>
              <TableCell colSpan={3} sx={{ fontWeight: 'bold' }}>
                Total
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                {formatCurrency(currentPortfolio.total_cost)}
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                {formatCurrency(currentPortfolio.total_value)}
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
                  {currentPortfolio.total_pnl >= 0 ? (
                    <TrendingUp color="success" fontSize="small" sx={{ mr: 0.5 }} />
                  ) : (
                    <TrendingDown color="error" fontSize="small" sx={{ mr: 0.5 }} />
                  )}
                  <Typography
                    color={`${getPerformanceColor(currentPortfolio.total_pnl)}.main`}
                    sx={{ fontWeight: 'bold' }}
                  >
                    {formatCurrency(currentPortfolio.total_pnl)}
                  </Typography>
                </Box>
                <Typography
                  variant="caption"
                  color={`${getPerformanceColor(currentPortfolio.total_pnl_percent)}.main`}
                  sx={{ fontWeight: 'bold' }}
                >
                  ({formatPercent(currentPortfolio.total_pnl_percent)})
                </Typography>
              </TableCell>
              <TableCell align="right" sx={{ fontWeight: 'bold' }}>
                100.00%
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
      
      <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
        Last updated: {currentPortfolio.last_updated 
          ? new Date(currentPortfolio.last_updated).toLocaleString()
          : 'N/A'
        }
      </Typography>
    </Box>
  );
};

export default PortfolioOverview;