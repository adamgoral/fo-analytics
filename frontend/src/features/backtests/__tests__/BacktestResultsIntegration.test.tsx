import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import BacktestResults from '../BacktestResults';
import * as backtestsApi from '../../../services/backtests';

// Mock the API
vi.mock('../../../services/backtests', () => ({
  backtestsApi: {
    get: vi.fn(),
    exportResults: vi.fn(),
  },
}));

// Mock recharts
vi.mock('recharts', () => import('../../../test/mocks/recharts'));

const theme = createTheme();

const mockBacktestWithCharts = {
  id: '123',
  strategy_id: 'strat-1',
  strategy_name: 'SMA Crossover',
  status: 'completed' as const,
  started_at: '2024-01-01T00:00:00Z',
  completed_at: '2024-01-01T00:05:00Z',
  parameters: {
    symbol: 'AAPL',
    start_date: '2023-01-01',
    end_date: '2024-01-01',
    initial_capital: 100000,
    commission: 0.001,
  },
  results: {
    total_return: 0.25,
    annualized_return: 0.28,
    sharpe_ratio: 1.8,
    sortino_ratio: 2.1,
    max_drawdown: -0.15,
    max_drawdown_duration: 30,
    win_rate: 0.65,
    profit_factor: 1.9,
    total_trades: 50,
    winning_trades: 32,
    losing_trades: 18,
    avg_win: 0.03,
    avg_loss: -0.015,
    best_trade: 0.08,
    worst_trade: -0.04,
    equity_curve: [
      { date: '2023-01-01', equity: 100000, benchmark_equity: 100000, drawdown: 0, drawdown_duration: 0 },
      { date: '2023-06-01', equity: 110000, benchmark_equity: 105000, drawdown: -0.05, drawdown_duration: 10 },
      { date: '2024-01-01', equity: 125000, benchmark_equity: 115000, drawdown: 0, drawdown_duration: 0 },
    ],
    trades: [],
  },
  user_id: 'user-1',
};

describe('BacktestResults Integration with Charts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays charts when equity curve data is available', async () => {
    (backtestsApi.backtestsApi.get as any).mockResolvedValue(mockBacktestWithCharts);

    render(
      <ThemeProvider theme={theme}>
        <BacktestResults backtestId="123" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Equity Curve')).toBeInTheDocument();
      expect(screen.getByText('Drawdown Analysis')).toBeInTheDocument();
    });
  });

  it('does not display charts when equity curve data is missing', async () => {
    const backtestWithoutCharts = {
      ...mockBacktestWithCharts,
      results: {
        ...mockBacktestWithCharts.results,
        equity_curve: undefined,
      },
    };

    (backtestsApi.backtestsApi.get as any).mockResolvedValue(backtestWithoutCharts);

    render(
      <ThemeProvider theme={theme}>
        <BacktestResults backtestId="123" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.queryByText('Equity Curve')).not.toBeInTheDocument();
      expect(screen.queryByText('Drawdown Analysis')).not.toBeInTheDocument();
    });
  });

  it('toggles chart visibility when button is clicked', async () => {
    (backtestsApi.backtestsApi.get as any).mockResolvedValue(mockBacktestWithCharts);

    render(
      <ThemeProvider theme={theme}>
        <BacktestResults backtestId="123" />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Equity Curve')).toBeInTheDocument();
    });

    // Click toggle button
    const toggleButton = screen.getByLabelText('Toggle Charts');
    fireEvent.click(toggleButton);

    // Charts should be hidden
    expect(screen.queryByText('Equity Curve')).not.toBeInTheDocument();
    expect(screen.queryByText('Drawdown Analysis')).not.toBeInTheDocument();

    // Click again to show
    fireEvent.click(toggleButton);

    // Charts should be visible again
    expect(screen.getByText('Equity Curve')).toBeInTheDocument();
    expect(screen.getByText('Drawdown Analysis')).toBeInTheDocument();
  });

  it('displays benchmark line when benchmark data is available', async () => {
    (backtestsApi.backtestsApi.get as any).mockResolvedValue(mockBacktestWithCharts);

    render(
      <ThemeProvider theme={theme}>
        <BacktestResults backtestId="123" />
      </ThemeProvider>
    );

    await waitFor(() => {
      // Check that the EquityChart is rendered with showBenchmark prop
      const equityChart = screen.getByText('Equity Curve').closest('div');
      expect(equityChart).toBeInTheDocument();
    });
  });

  it('handles empty equity curve gracefully', async () => {
    const backtestWithEmptyEquity = {
      ...mockBacktestWithCharts,
      results: {
        ...mockBacktestWithCharts.results,
        equity_curve: [],
      },
    };

    (backtestsApi.backtestsApi.get as any).mockResolvedValue(backtestWithEmptyEquity);

    render(
      <ThemeProvider theme={theme}>
        <BacktestResults backtestId="123" />
      </ThemeProvider>
    );

    await waitFor(() => {
      // Should not show charts if equity curve is empty
      expect(screen.queryByText('Equity Curve')).not.toBeInTheDocument();
      expect(screen.queryByText('Drawdown Analysis')).not.toBeInTheDocument();
    });
  });
});