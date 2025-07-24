import { describe, it, expect, vi, beforeEach } from 'vitest';
import { backtestsApi } from '../backtests';
import { apiClient } from '../api';

// Mock the apiClient
vi.mock('../api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock window.URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
global.URL.revokeObjectURL = vi.fn();

// Mock document.createElement and appendChild
const mockLink = {
  href: '',
  setAttribute: vi.fn(),
  click: vi.fn(),
  remove: vi.fn(),
};

document.createElement = vi.fn(() => mockLink as any);
document.body.appendChild = vi.fn();

describe('backtestsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('list', () => {
    it('should fetch all backtests', async () => {
      const mockBacktests = [
        { id: '1', strategy_name: 'Strategy 1' },
        { id: '2', strategy_name: 'Strategy 2' },
      ];
      vi.mocked(apiClient.get).mockResolvedValue(mockBacktests);

      const result = await backtestsApi.list();

      expect(apiClient.get).toHaveBeenCalledWith('/backtests');
      expect(result).toEqual(mockBacktests);
    });
  });

  describe('get', () => {
    it('should fetch a single backtest by id', async () => {
      const mockBacktest = {
        id: '1',
        strategy_name: 'Test Strategy',
        status: 'completed',
        results: { total_return: 0.15 },
      };
      vi.mocked(apiClient.get).mockResolvedValue(mockBacktest);

      const result = await backtestsApi.get('1');

      expect(apiClient.get).toHaveBeenCalledWith('/backtests/1');
      expect(result).toEqual(mockBacktest);
    });
  });

  describe('create', () => {
    it('should create a new backtest with required parameters', async () => {
      const params = {
        strategy_id: 'strategy123',
      };
      const mockResponse = {
        id: 'backtest123',
        strategy_id: 'strategy123',
        status: 'pending',
      };
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await backtestsApi.create(params);

      expect(apiClient.post).toHaveBeenCalledWith('/backtests', params);
      expect(result).toEqual(mockResponse);
    });

    it('should create a new backtest with all parameters', async () => {
      const params = {
        strategy_id: 'strategy123',
        symbol: 'AAPL',
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        initial_capital: 100000,
        commission: 0.001,
      };
      const mockResponse = { id: 'backtest123', status: 'pending' };
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await backtestsApi.create(params);

      expect(apiClient.post).toHaveBeenCalledWith('/backtests', params);
      expect(result).toEqual(mockResponse);
    });
  });

  describe('getStrategyTypes', () => {
    it('should fetch available strategy types', async () => {
      const mockStrategyTypes = [
        { type: 'sma_crossover', name: 'SMA Crossover', description: 'Simple moving average crossover' },
        { type: 'rsi', name: 'RSI Strategy', description: 'Relative strength index strategy' },
      ];
      vi.mocked(apiClient.get).mockResolvedValue(mockStrategyTypes);

      const result = await backtestsApi.getStrategyTypes();

      expect(apiClient.get).toHaveBeenCalledWith('/backtests/strategy-types');
      expect(result).toEqual(mockStrategyTypes);
    });
  });

  describe('delete', () => {
    it('should delete a backtest by id', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue(undefined);

      await backtestsApi.delete('backtest123');

      expect(apiClient.delete).toHaveBeenCalledWith('/backtests/backtest123');
    });
  });

  describe('exportResults', () => {
    it('should export backtest results to CSV', async () => {
      const mockBacktest = {
        id: 'backtest123',
        results: {
          total_return: 0.25,
          annualized_return: 0.28,
          sharpe_ratio: 1.8,
          sortino_ratio: 2.1,
          max_drawdown: -0.15,
          win_rate: 0.65,
          total_trades: 50,
          profit_factor: 2.5,
        },
      };
      vi.mocked(apiClient.get).mockResolvedValue(mockBacktest);

      await backtestsApi.exportResults('backtest123');

      expect(apiClient.get).toHaveBeenCalledWith('/backtests/backtest123');
      
      // Verify CSV creation and download
      expect(global.URL.createObjectURL).toHaveBeenCalledWith(expect.any(Blob));
      expect(mockLink.setAttribute).toHaveBeenCalledWith('download', 'backtest_backtest123_results.csv');
      expect(mockLink.click).toHaveBeenCalled();
      expect(mockLink.remove).toHaveBeenCalled();
      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url');
    });

    it('should throw error when no results available', async () => {
      const mockBacktest = {
        id: 'backtest123',
        results: undefined,
      };
      vi.mocked(apiClient.get).mockResolvedValue(mockBacktest);

      await expect(backtestsApi.exportResults('backtest123')).rejects.toThrow(
        'No results available for export'
      );

      expect(apiClient.get).toHaveBeenCalledWith('/backtests/backtest123');
    });

    it('should generate correct CSV content', async () => {
      const mockBacktest = {
        id: 'backtest123',
        results: {
          total_return: 0.25,
          annualized_return: 0.28,
          sharpe_ratio: 1.8,
          sortino_ratio: 2.1,
          max_drawdown: -0.15,
          win_rate: 0.65,
          total_trades: 50,
          profit_factor: 2.5,
        },
      };
      vi.mocked(apiClient.get).mockResolvedValue(mockBacktest);

      let blobContent = '';
      global.Blob = vi.fn().mockImplementation((content) => {
        blobContent = content[0];
        return { size: content[0].length, type: 'text/csv' };
      }) as any;

      await backtestsApi.exportResults('backtest123');

      expect(blobContent).toContain('Metric,Value');
      expect(blobContent).toContain('Total Return,25.00%');
      expect(blobContent).toContain('Annualized Return,28.00%');
      expect(blobContent).toContain('Sharpe Ratio,1.80');
      expect(blobContent).toContain('Sortino Ratio,2.10');
      expect(blobContent).toContain('Max Drawdown,-15.00%');
      expect(blobContent).toContain('Win Rate,65.00%');
      expect(blobContent).toContain('Total Trades,50');
      expect(blobContent).toContain('Profit Factor,2.50');
    });
  });
});