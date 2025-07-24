import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import BacktestResults from '../BacktestResults';
import { backtestsApi } from '../../../services/backtests';

// Mock the API service
vi.mock('../../../services/backtests', () => ({
  backtestsApi: {
    get: vi.fn(),
    exportResults: vi.fn(),
  },
}));

const mockBacktestResult = {
  id: 'backtest123',
  strategy_id: 'strategy123',
  strategy_name: 'SMA Crossover Strategy',
  status: 'completed' as const,
  started_at: '2024-01-01T00:00:00Z',
  completed_at: '2024-01-01T01:00:00Z',
  parameters: {
    symbol: 'AAPL',
    start_date: '2023-01-01',
    end_date: '2023-12-31',
    initial_capital: 100000,
    commission: 0.001,
  },
  results: {
    total_return: 0.25,
    annualized_return: 0.28,
    sharpe_ratio: 1.8,
    sortino_ratio: 2.1,
    max_drawdown: -0.15,
    win_rate: 0.65,
    profit_factor: 2.5,
    total_trades: 50,
    winning_trades: 32,
    losing_trades: 18,
    avg_win: 0.03,
    avg_loss: -0.015,
    best_trade: 0.08,
    worst_trade: -0.04,
    equity_curve: [
      { date: '2023-01-01', value: 100000 },
      { date: '2023-12-31', value: 125000 },
    ],
    drawdown_curve: [
      { date: '2023-01-01', value: 0 },
      { date: '2023-06-15', value: -0.15 },
    ],
    trades: [
      {
        entry_date: '2023-01-15',
        exit_date: '2023-01-20',
        entry_price: 150,
        exit_price: 155,
        size: 100,
        pnl: 500,
        return_pct: 0.033,
        duration_days: 5,
      },
      {
        entry_date: '2023-02-01',
        exit_date: '2023-02-05',
        entry_price: 160,
        exit_price: 158,
        size: 100,
        pnl: -200,
        return_pct: -0.0125,
        duration_days: 4,
      },
    ],
  },
  user_id: 'user123',
};

describe('BacktestResults', () => {
  const mockProps = {
    backtestId: 'backtest123',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render loading state initially', () => {
    render(<BacktestResults {...mockProps} />);
    expect(screen.getByText('Loading backtest results...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should load and display backtest results', async () => {
    vi.mocked(backtestsApi.get).mockResolvedValue(mockBacktestResult);

    render(<BacktestResults {...mockProps} />);

    await waitFor(() => {
      expect(backtestsApi.get).toHaveBeenCalledWith('backtest123');
    });

    // Check header information
    expect(screen.getByText('Backtest Results')).toBeInTheDocument();
    expect(screen.getByText('SMA Crossover Strategy • AAPL')).toBeInTheDocument();

    // Check key metrics
    expect(screen.getByText('25.00%')).toBeInTheDocument(); // Total return
    expect(screen.getByText('1.80')).toBeInTheDocument(); // Sharpe ratio
    expect(screen.getByText('-15.00%')).toBeInTheDocument(); // Max drawdown
    expect(screen.getByText('65.00%')).toBeInTheDocument(); // Win rate
  });

  it('should display error state when loading fails', async () => {
    const errorMessage = 'Failed to load backtest results';
    vi.mocked(backtestsApi.get).mockRejectedValue(new Error(errorMessage));

    render(<BacktestResults {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    // Check if retry button is present
    const retryButton = screen.getByText('Retry');
    expect(retryButton).toBeInTheDocument();

    // Test retry functionality
    vi.mocked(backtestsApi.get).mockResolvedValue(mockBacktestResult);
    fireEvent.click(retryButton);

    await waitFor(() => {
      expect(backtestsApi.get).toHaveBeenCalledTimes(2);
    });
  });

  it('should display running state for in-progress backtests', async () => {
    const runningBacktest = {
      ...mockBacktestResult,
      status: 'running' as const,
      results: undefined,
    };

    vi.mocked(backtestsApi.get).mockResolvedValue(runningBacktest);

    render(<BacktestResults {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Backtest is currently running...')).toBeInTheDocument();
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });
  });

  it('should display failed state with error message', async () => {
    const failedBacktest = {
      ...mockBacktestResult,
      status: 'failed' as const,
      results: undefined,
      error: 'Insufficient data for backtesting',
    };

    vi.mocked(backtestsApi.get).mockResolvedValue(failedBacktest);

    render(<BacktestResults {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Insufficient data for backtesting')).toBeInTheDocument();
    });
  });

  it('should export results when export button is clicked', async () => {
    vi.mocked(backtestsApi.get).mockResolvedValue(mockBacktestResult);

    render(<BacktestResults {...mockProps} />);

    await waitFor(() => {
      const exportButton = screen.getByLabelText('Export Results');
      fireEvent.click(exportButton);
    });

    expect(backtestsApi.exportResults).toHaveBeenCalledWith('backtest123');
  });

  it('should display all performance metrics correctly', async () => {
    vi.mocked(backtestsApi.get).mockResolvedValue(mockBacktestResult);

    render(<BacktestResults {...mockProps} />);

    await waitFor(() => {
      // Additional metrics
      expect(screen.getByText('28.00%')).toBeInTheDocument(); // Annualized return
      expect(screen.getByText('2.10')).toBeInTheDocument(); // Sortino ratio
      expect(screen.getByText('2.50')).toBeInTheDocument(); // Profit factor
      expect(screen.getByText('3.00%')).toBeInTheDocument(); // Average win
      expect(screen.getByText('-1.50%')).toBeInTheDocument(); // Average loss
      expect(screen.getByText('8.00%')).toBeInTheDocument(); // Best trade
    });
  });

  it('should display trade history table', async () => {
    vi.mocked(backtestsApi.get).mockResolvedValue(mockBacktestResult);

    render(<BacktestResults {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Trade History')).toBeInTheDocument();
    });

    // Check table headers
    expect(screen.getByText('Entry Date')).toBeInTheDocument();
    expect(screen.getByText('Exit Date')).toBeInTheDocument();
    expect(screen.getByText('P&L')).toBeInTheDocument();
    expect(screen.getByText('Return')).toBeInTheDocument();

    // Check trade data
    expect(screen.getByText('$500')).toBeInTheDocument();
    expect(screen.getByText('3.30%')).toBeInTheDocument();
    expect(screen.getByText('-$200')).toBeInTheDocument();
    expect(screen.getByText('-1.25%')).toBeInTheDocument();
  });

  it('should toggle between showing recent and all trades', async () => {
    const manyTrades = Array.from({ length: 20 }, (_, i) => ({
      ...mockBacktestResult.results.trades[0],
      entry_date: `2023-01-${(i + 1).toString().padStart(2, '0')}`,
    }));

    const backtestWithManyTrades = {
      ...mockBacktestResult,
      results: {
        ...mockBacktestResult.results,
        trades: manyTrades,
      },
    };

    vi.mocked(backtestsApi.get).mockResolvedValue(backtestWithManyTrades);

    render(<BacktestResults {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Showing 10 of 20 trades')).toBeInTheDocument();
    });

    // Click show all button
    const showAllButton = screen.getByText('Show All');
    fireEvent.click(showAllButton);

    // Should now show all trades
    expect(screen.queryByText('Showing 10 of 20 trades')).not.toBeInTheDocument();
    expect(screen.getByText('Show Recent')).toBeInTheDocument();
  });

  it('should format currency values correctly', async () => {
    vi.mocked(backtestsApi.get).mockResolvedValue(mockBacktestResult);

    render(<BacktestResults {...mockProps} />);

    await waitFor(() => {
      expect(screen.getByText('Initial Capital: $100,000')).toBeInTheDocument();
    });
  });

  it('should display metrics with correct values', async () => {
    vi.mocked(backtestsApi.get).mockResolvedValue(mockBacktestResult);

    render(<BacktestResults {...mockProps} />);

    await waitFor(() => {
      // Check that positive and negative metrics are displayed
      expect(screen.getByText('25.00%')).toBeInTheDocument(); // Total return
      expect(screen.getByText('-15.00%')).toBeInTheDocument(); // Max drawdown
    });
  });
});