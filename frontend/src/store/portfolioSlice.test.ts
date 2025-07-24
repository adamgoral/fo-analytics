import { configureStore } from '@reduxjs/toolkit';
import portfolioReducer, {
  setSelectedTab,
  setSelectedOptimizationMethod,
  setCurrentPortfolio,
  clearOptimizationResult,
  clearEfficientFrontier,
  clearMultiStrategyResult,
  clearRiskMetrics,
  optimizePortfolio,
  calculateEfficientFrontier,
  runMultiStrategyBacktest,
  calculateRiskMetrics,
  fetchOptimizationMethods,
} from './portfolioSlice';
import { mockPortfolioData } from '../features/portfolio/mockData';
import {
  mockOptimizationResult,
  mockEfficientFrontierData,
  mockMultiStrategyResult,
  mockRiskMetricsData,
} from '../features/portfolio/test-utils';
import portfolioService from '../services/portfolio';

// Mock the portfolio service
jest.mock('../services/portfolio');
const mockedPortfolioService = portfolioService as jest.Mocked<typeof portfolioService>;

describe('portfolioSlice', () => {
  let store: ReturnType<typeof configureStore>;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        portfolio: portfolioReducer,
      },
    });
    jest.clearAllMocks();
  });

  describe('synchronous actions', () => {
    it('should handle setSelectedTab', () => {
      store.dispatch(setSelectedTab(2));
      const state = store.getState().portfolio;
      expect(state.selectedTab).toBe(2);
    });

    it('should handle setSelectedOptimizationMethod', () => {
      store.dispatch(setSelectedOptimizationMethod('max_sharpe'));
      const state = store.getState().portfolio;
      expect(state.selectedOptimizationMethod).toBe('max_sharpe');
    });

    it('should handle setCurrentPortfolio', () => {
      store.dispatch(setCurrentPortfolio(mockPortfolioData));
      const state = store.getState().portfolio;
      expect(state.currentPortfolio).toEqual(mockPortfolioData);
    });

    it('should handle clearOptimizationResult', () => {
      // First set a result
      store.dispatch({
        type: optimizePortfolio.fulfilled.type,
        payload: mockOptimizationResult,
      });
      
      // Then clear it
      store.dispatch(clearOptimizationResult());
      const state = store.getState().portfolio;
      expect(state.optimization.result).toBeNull();
      expect(state.optimization.error).toBeNull();
    });

    it('should handle clearEfficientFrontier', () => {
      // First set data
      store.dispatch({
        type: calculateEfficientFrontier.fulfilled.type,
        payload: mockEfficientFrontierData,
      });
      
      // Then clear it
      store.dispatch(clearEfficientFrontier());
      const state = store.getState().portfolio;
      expect(state.efficientFrontier.data).toBeNull();
      expect(state.efficientFrontier.error).toBeNull();
    });

    it('should handle clearMultiStrategyResult', () => {
      // First set result
      store.dispatch({
        type: runMultiStrategyBacktest.fulfilled.type,
        payload: mockMultiStrategyResult,
      });
      
      // Then clear it
      store.dispatch(clearMultiStrategyResult());
      const state = store.getState().portfolio;
      expect(state.multiStrategyBacktest.result).toBeNull();
      expect(state.multiStrategyBacktest.error).toBeNull();
    });

    it('should handle clearRiskMetrics', () => {
      // First set data
      store.dispatch({
        type: calculateRiskMetrics.fulfilled.type,
        payload: mockRiskMetricsData,
      });
      
      // Then clear it
      store.dispatch(clearRiskMetrics());
      const state = store.getState().portfolio;
      expect(state.riskMetrics.data).toBeNull();
      expect(state.riskMetrics.error).toBeNull();
    });
  });

  describe('optimizePortfolio async thunk', () => {
    it('should handle optimizePortfolio.pending', () => {
      store.dispatch({ type: optimizePortfolio.pending.type });
      const state = store.getState().portfolio;
      expect(state.optimization.loading).toBe(true);
      expect(state.optimization.error).toBeNull();
    });

    it('should handle optimizePortfolio.fulfilled', () => {
      store.dispatch({
        type: optimizePortfolio.fulfilled.type,
        payload: mockOptimizationResult,
      });
      const state = store.getState().portfolio;
      expect(state.optimization.loading).toBe(false);
      expect(state.optimization.result).toEqual(mockOptimizationResult);
      expect(state.optimization.error).toBeNull();
    });

    it('should handle optimizePortfolio.rejected', () => {
      const errorMessage = 'Optimization failed';
      store.dispatch({
        type: optimizePortfolio.rejected.type,
        error: { message: errorMessage },
      });
      const state = store.getState().portfolio;
      expect(state.optimization.loading).toBe(false);
      expect(state.optimization.result).toBeNull();
      expect(state.optimization.error).toBe(errorMessage);
    });

    it('should make API call with correct parameters', async () => {
      mockedPortfolioService.optimizePortfolio.mockResolvedValue(mockOptimizationResult);
      
      const request = {
        symbols: ['AAPL', 'GOOGL'],
        start_date: '2023-01-01',
        end_date: '2023-12-31',
        method: 'mean_variance' as const,
      };
      
      await store.dispatch(optimizePortfolio(request));
      
      expect(mockedPortfolioService.optimizePortfolio).toHaveBeenCalledWith(request);
    });
  });

  describe('calculateEfficientFrontier async thunk', () => {
    it('should handle calculateEfficientFrontier.pending', () => {
      store.dispatch({ type: calculateEfficientFrontier.pending.type });
      const state = store.getState().portfolio;
      expect(state.efficientFrontier.loading).toBe(true);
      expect(state.efficientFrontier.error).toBeNull();
    });

    it('should handle calculateEfficientFrontier.fulfilled', () => {
      store.dispatch({
        type: calculateEfficientFrontier.fulfilled.type,
        payload: mockEfficientFrontierData,
      });
      const state = store.getState().portfolio;
      expect(state.efficientFrontier.loading).toBe(false);
      expect(state.efficientFrontier.data).toEqual(mockEfficientFrontierData);
      expect(state.efficientFrontier.error).toBeNull();
    });

    it('should handle calculateEfficientFrontier.rejected', () => {
      const errorMessage = 'Calculation failed';
      store.dispatch({
        type: calculateEfficientFrontier.rejected.type,
        error: { message: errorMessage },
      });
      const state = store.getState().portfolio;
      expect(state.efficientFrontier.loading).toBe(false);
      expect(state.efficientFrontier.data).toBeNull();
      expect(state.efficientFrontier.error).toBe(errorMessage);
    });
  });

  describe('runMultiStrategyBacktest async thunk', () => {
    it('should handle runMultiStrategyBacktest.pending', () => {
      store.dispatch({ type: runMultiStrategyBacktest.pending.type });
      const state = store.getState().portfolio;
      expect(state.multiStrategyBacktest.loading).toBe(true);
      expect(state.multiStrategyBacktest.error).toBeNull();
    });

    it('should handle runMultiStrategyBacktest.fulfilled', () => {
      store.dispatch({
        type: runMultiStrategyBacktest.fulfilled.type,
        payload: mockMultiStrategyResult,
      });
      const state = store.getState().portfolio;
      expect(state.multiStrategyBacktest.loading).toBe(false);
      expect(state.multiStrategyBacktest.result).toEqual(mockMultiStrategyResult);
      expect(state.multiStrategyBacktest.error).toBeNull();
    });

    it('should handle runMultiStrategyBacktest.rejected', () => {
      const errorMessage = 'Backtest failed';
      store.dispatch({
        type: runMultiStrategyBacktest.rejected.type,
        error: { message: errorMessage },
      });
      const state = store.getState().portfolio;
      expect(state.multiStrategyBacktest.loading).toBe(false);
      expect(state.multiStrategyBacktest.result).toBeNull();
      expect(state.multiStrategyBacktest.error).toBe(errorMessage);
    });
  });

  describe('calculateRiskMetrics async thunk', () => {
    it('should handle calculateRiskMetrics.pending', () => {
      store.dispatch({ type: calculateRiskMetrics.pending.type });
      const state = store.getState().portfolio;
      expect(state.riskMetrics.loading).toBe(true);
      expect(state.riskMetrics.error).toBeNull();
    });

    it('should handle calculateRiskMetrics.fulfilled', () => {
      store.dispatch({
        type: calculateRiskMetrics.fulfilled.type,
        payload: mockRiskMetricsData,
      });
      const state = store.getState().portfolio;
      expect(state.riskMetrics.loading).toBe(false);
      expect(state.riskMetrics.data).toEqual(mockRiskMetricsData);
      expect(state.riskMetrics.error).toBeNull();
    });

    it('should handle calculateRiskMetrics.rejected', () => {
      const errorMessage = 'Risk calculation failed';
      store.dispatch({
        type: calculateRiskMetrics.rejected.type,
        error: { message: errorMessage },
      });
      const state = store.getState().portfolio;
      expect(state.riskMetrics.loading).toBe(false);
      expect(state.riskMetrics.data).toBeNull();
      expect(state.riskMetrics.error).toBe(errorMessage);
    });
  });

  describe('fetchOptimizationMethods async thunk', () => {
    const mockMethods = {
      mean_variance: {
        name: 'Mean-Variance Optimization',
        description: 'Classic Markowitz optimization',
        parameters: [],
      },
      max_sharpe: {
        name: 'Maximum Sharpe Ratio',
        description: 'Maximize risk-adjusted returns',
        parameters: [],
      },
    };

    it('should handle fetchOptimizationMethods.fulfilled', () => {
      store.dispatch({
        type: fetchOptimizationMethods.fulfilled.type,
        payload: mockMethods,
      });
      const state = store.getState().portfolio;
      expect(state.optimizationMethods).toEqual(mockMethods);
    });

    it('should make API call to fetch methods', async () => {
      mockedPortfolioService.getOptimizationMethods.mockResolvedValue(mockMethods);
      
      await store.dispatch(fetchOptimizationMethods());
      
      expect(mockedPortfolioService.getOptimizationMethods).toHaveBeenCalled();
    });
  });

  describe('initial state', () => {
    it('should have correct initial state', () => {
      const state = store.getState().portfolio;
      
      expect(state.optimization.result).toBeNull();
      expect(state.optimization.loading).toBe(false);
      expect(state.optimization.error).toBeNull();
      
      expect(state.efficientFrontier.data).toBeNull();
      expect(state.efficientFrontier.loading).toBe(false);
      expect(state.efficientFrontier.error).toBeNull();
      
      expect(state.multiStrategyBacktest.result).toBeNull();
      expect(state.multiStrategyBacktest.loading).toBe(false);
      expect(state.multiStrategyBacktest.error).toBeNull();
      
      expect(state.riskMetrics.data).toBeNull();
      expect(state.riskMetrics.loading).toBe(false);
      expect(state.riskMetrics.error).toBeNull();
      
      expect(state.optimizationMethods).toBeNull();
      expect(state.currentPortfolio).toBeNull();
      expect(state.selectedTab).toBe(0);
      expect(state.selectedOptimizationMethod).toBe('mean_variance');
    });
  });

  describe('error handling', () => {
    it('should use default error message when none provided', () => {
      store.dispatch({
        type: optimizePortfolio.rejected.type,
        error: {},
      });
      const state = store.getState().portfolio;
      expect(state.optimization.error).toBe('Portfolio optimization failed');
    });

    it('should handle multiple errors independently', () => {
      // Set different errors for different operations
      store.dispatch({
        type: optimizePortfolio.rejected.type,
        error: { message: 'Optimization error' },
      });
      store.dispatch({
        type: calculateEfficientFrontier.rejected.type,
        error: { message: 'Frontier error' },
      });
      
      const state = store.getState().portfolio;
      expect(state.optimization.error).toBe('Optimization error');
      expect(state.efficientFrontier.error).toBe('Frontier error');
    });
  });
});