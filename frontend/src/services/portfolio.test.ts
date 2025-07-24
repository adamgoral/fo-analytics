import portfolioService from './portfolio';
import api from './api';
import {
  mockOptimizationResult,
  mockEfficientFrontierData,
  mockMultiStrategyResult,
  mockRiskMetricsData,
} from '../features/portfolio/test-utils';

// Mock the api module
jest.mock('./api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('PortfolioService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('optimizePortfolio', () => {
    it('should call API with correct endpoint and data', async () => {
      const request = {
        symbols: ['AAPL', 'GOOGL', 'MSFT'],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        method: 'mean_variance' as const,
        target_return: 0.15,
        risk_free_rate: 0.02,
      };

      mockedApi.post.mockResolvedValue({ data: mockOptimizationResult });

      const result = await portfolioService.optimizePortfolio(request);

      expect(mockedApi.post).toHaveBeenCalledWith('/portfolio/optimize', request);
      expect(result).toEqual(mockOptimizationResult);
    });

    it('should handle API errors', async () => {
      const request = {
        symbols: ['AAPL'],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        method: 'mean_variance' as const,
      };

      const error = new Error('API Error');
      mockedApi.post.mockRejectedValue(error);

      await expect(portfolioService.optimizePortfolio(request)).rejects.toThrow('API Error');
    });
  });

  describe('calculateEfficientFrontier', () => {
    it('should call API with correct endpoint and data', async () => {
      const request = {
        symbols: ['AAPL', 'GOOGL', 'MSFT', 'AMZN'],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        risk_free_rate: 0.02,
        n_portfolios: 50,
      };

      mockedApi.post.mockResolvedValue({ data: mockEfficientFrontierData });

      const result = await portfolioService.calculateEfficientFrontier(request);

      expect(mockedApi.post).toHaveBeenCalledWith('/portfolio/efficient-frontier', request);
      expect(result).toEqual(mockEfficientFrontierData);
    });

    it('should use default values when optional params not provided', async () => {
      const request = {
        symbols: ['AAPL', 'GOOGL'],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
      };

      mockedApi.post.mockResolvedValue({ data: mockEfficientFrontierData });

      await portfolioService.calculateEfficientFrontier(request);

      expect(mockedApi.post).toHaveBeenCalledWith('/portfolio/efficient-frontier', request);
    });
  });

  describe('runMultiStrategyBacktest', () => {
    it('should call API with correct endpoint and data', async () => {
      const request = {
        strategies: [
          {
            strategy_type: 'sma_crossover',
            parameters: { fast_period: 10, slow_period: 30 },
            weight: 0.5,
          },
          {
            strategy_type: 'rsi_mean_reversion',
            parameters: { rsi_period: 14, oversold: 30, overbought: 70 },
            weight: 0.5,
          },
        ],
        symbols: ['SPY', 'QQQ'],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        initial_capital: 100000,
        optimization_method: 'mean_variance' as const,
        rebalance_frequency: 'monthly' as const,
      };

      mockedApi.post.mockResolvedValue({ data: mockMultiStrategyResult });

      const result = await portfolioService.runMultiStrategyBacktest(request);

      expect(mockedApi.post).toHaveBeenCalledWith('/portfolio/multi-strategy-backtest', request);
      expect(result).toEqual(mockMultiStrategyResult);
    });

    it('should work with minimal required parameters', async () => {
      const request = {
        strategies: [
          {
            strategy_type: 'momentum',
            parameters: { lookback_period: 20 },
            weight: 1.0,
          },
        ],
        symbols: ['SPY'],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
      };

      mockedApi.post.mockResolvedValue({ data: mockMultiStrategyResult });

      await portfolioService.runMultiStrategyBacktest(request);

      expect(mockedApi.post).toHaveBeenCalledWith('/portfolio/multi-strategy-backtest', request);
    });
  });

  describe('calculateRiskMetrics', () => {
    it('should call API with correct endpoint and data', async () => {
      const request = {
        returns: [0.01, -0.02, 0.03, -0.01, 0.02],
        benchmark_returns: [0.008, -0.015, 0.025, -0.005, 0.018],
        confidence_level: 0.95,
        risk_free_rate: 0.02,
      };

      mockedApi.post.mockResolvedValue({ data: mockRiskMetricsData });

      const result = await portfolioService.calculateRiskMetrics(request);

      expect(mockedApi.post).toHaveBeenCalledWith('/portfolio/risk-metrics', request);
      expect(result).toEqual(mockRiskMetricsData);
    });

    it('should work without optional benchmark returns', async () => {
      const request = {
        returns: [0.01, -0.02, 0.03, -0.01, 0.02],
      };

      const metricsWithoutRelative = {
        ...mockRiskMetricsData,
        relative_metrics: undefined,
      };

      mockedApi.post.mockResolvedValue({ data: metricsWithoutRelative });

      const result = await portfolioService.calculateRiskMetrics(request);

      expect(mockedApi.post).toHaveBeenCalledWith('/portfolio/risk-metrics', request);
      expect(result.relative_metrics).toBeUndefined();
    });
  });

  describe('getOptimizationMethods', () => {
    it('should call API with correct endpoint', async () => {
      const mockMethods = {
        mean_variance: {
          name: 'Mean-Variance Optimization',
          description: 'Classic Markowitz optimization',
          parameters: [
            {
              name: 'target_return',
              type: 'float',
              required: false,
              description: 'Target annual return',
            },
          ],
        },
        max_sharpe: {
          name: 'Maximum Sharpe Ratio',
          description: 'Maximize risk-adjusted returns',
          parameters: [
            {
              name: 'risk_free_rate',
              type: 'float',
              required: false,
              description: 'Risk-free rate for Sharpe calculation',
            },
          ],
        },
        min_volatility: {
          name: 'Minimum Volatility',
          description: 'Find the lowest risk portfolio',
          parameters: [],
        },
        risk_parity: {
          name: 'Risk Parity',
          description: 'Equal risk contribution from each asset',
          parameters: [],
        },
        black_litterman: {
          name: 'Black-Litterman',
          description: 'Combine market equilibrium with views',
          parameters: [
            {
              name: 'views',
              type: 'array',
              required: true,
              description: 'Market views',
            },
            {
              name: 'view_confidences',
              type: 'array',
              required: true,
              description: 'Confidence in each view',
            },
          ],
        },
      };

      mockedApi.get.mockResolvedValue({ data: mockMethods });

      const result = await portfolioService.getOptimizationMethods();

      expect(mockedApi.get).toHaveBeenCalledWith('/portfolio/optimization-methods');
      expect(result).toEqual(mockMethods);
    });

    it('should handle empty response', async () => {
      mockedApi.get.mockResolvedValue({ data: {} });

      const result = await portfolioService.getOptimizationMethods();

      expect(result).toEqual({});
    });

    it('should handle API errors', async () => {
      const error = new Error('Network Error');
      mockedApi.get.mockRejectedValue(error);

      await expect(portfolioService.getOptimizationMethods()).rejects.toThrow('Network Error');
    });
  });

  describe('edge cases', () => {
    it('should handle empty symbols array', async () => {
      const request = {
        symbols: [],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        method: 'mean_variance' as const,
      };

      mockedApi.post.mockResolvedValue({ data: { error: 'No symbols provided' } });

      await portfolioService.optimizePortfolio(request);

      expect(mockedApi.post).toHaveBeenCalledWith('/portfolio/optimize', request);
    });

    it('should handle invalid date formats', async () => {
      const request = {
        symbols: ['AAPL'],
        start_date: 'invalid-date',
        end_date: '2023-12-31',
        method: 'mean_variance' as const,
      };

      mockedApi.post.mockResolvedValue({ data: { error: 'Invalid date format' } });

      await portfolioService.optimizePortfolio(request);

      expect(mockedApi.post).toHaveBeenCalledWith('/portfolio/optimize', request);
    });

    it('should handle very large returns array', async () => {
      const largeReturns = Array(10000).fill(0).map(() => Math.random() * 0.1 - 0.05);
      const request = {
        returns: largeReturns,
      };

      mockedApi.post.mockResolvedValue({ data: mockRiskMetricsData });

      await portfolioService.calculateRiskMetrics(request);

      expect(mockedApi.post).toHaveBeenCalledWith('/portfolio/risk-metrics', request);
    });
  });
});