import { apiClient } from './api';

export interface BacktestParameters {
  strategy_id: string;
  symbol?: string;
  start_date?: string;
  end_date?: string;
  initial_capital?: number;
  commission?: number;
}

export interface BacktestResult {
  id: string;
  strategy_id: string;
  strategy_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  parameters: {
    symbol: string;
    start_date: string;
    end_date: string;
    initial_capital: number;
    commission: number;
  };
  results?: {
    total_return: number;
    annualized_return: number;
    sharpe_ratio: number;
    sortino_ratio: number;
    max_drawdown: number;
    win_rate: number;
    profit_factor: number;
    total_trades: number;
    winning_trades: number;
    losing_trades: number;
    avg_win: number;
    avg_loss: number;
    best_trade: number;
    worst_trade: number;
    equity_curve: Array<{ date: string; value: number }>;
    drawdown_curve: Array<{ date: string; value: number }>;
    trades: Array<{
      entry_date: string;
      exit_date: string;
      entry_price: number;
      exit_price: number;
      size: number;
      pnl: number;
      return_pct: number;
      duration_days: number;
    }>;
  };
  error?: string;
  user_id: string;
}

export interface StrategyType {
  type: string;
  name: string;
  description: string;
  parameters: Record<string, any>;
}

export const backtestsApi = {
  // Get all backtests
  list: () => apiClient.get<BacktestResult[]>('/backtests'),

  // Get single backtest
  get: (id: string) => apiClient.get<BacktestResult>(`/backtests/${id}`),

  // Create new backtest
  create: (params: BacktestParameters) => 
    apiClient.post<BacktestResult>('/backtests', params),

  // Get available strategy types
  getStrategyTypes: () => 
    apiClient.get<StrategyType[]>('/backtests/strategy-types'),

  // Delete backtest
  delete: (id: string) => apiClient.delete(`/backtests/${id}`),

  // Export backtest results
  exportResults: async (id: string) => {
    const backtest = await backtestsApi.get(id);
    if (!backtest.results) {
      throw new Error('No results available for export');
    }

    const csvContent = [
      ['Metric', 'Value'],
      ['Total Return', `${(backtest.results.total_return * 100).toFixed(2)}%`],
      ['Annualized Return', `${(backtest.results.annualized_return * 100).toFixed(2)}%`],
      ['Sharpe Ratio', backtest.results.sharpe_ratio.toFixed(2)],
      ['Sortino Ratio', backtest.results.sortino_ratio.toFixed(2)],
      ['Max Drawdown', `${(backtest.results.max_drawdown * 100).toFixed(2)}%`],
      ['Win Rate', `${(backtest.results.win_rate * 100).toFixed(2)}%`],
      ['Total Trades', backtest.results.total_trades.toString()],
      ['Profit Factor', backtest.results.profit_factor.toFixed(2)],
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `backtest_${id}_results.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};