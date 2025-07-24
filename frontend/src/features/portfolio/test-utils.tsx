import React from 'react';
import { render } from '@testing-library/react';
import { Provider } from 'react-redux';
import { MemoryRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import portfolioReducer from '../../store/portfolioSlice';
import authReducer from '../../store/slices/authSlice';
import chatReducer from '../../store/slices/chatSlice';
import { mockPortfolioData } from './mockData';

export const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      chat: chatReducer,
      portfolio: portfolioReducer,
    },
    preloadedState: {
      auth: {
        user: { id: '1', email: 'test@example.com', role: 'analyst' },
        isAuthenticated: true,
        loading: false,
        error: null,
      },
      portfolio: {
        optimization: {
          result: null,
          loading: false,
          error: null,
        },
        efficientFrontier: {
          data: null,
          loading: false,
          error: null,
        },
        multiStrategyBacktest: {
          result: null,
          loading: false,
          error: null,
        },
        riskMetrics: {
          data: null,
          loading: false,
          error: null,
        },
        optimizationMethods: {
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
        },
        currentPortfolio: null,
        selectedTab: 0,
        selectedOptimizationMethod: 'mean_variance',
        ...initialState,
      },
    },
  });
};

export const renderWithProviders = (
  component: React.ReactElement,
  { initialState = {}, store = createMockStore(initialState), ...renderOptions } = {}
) => {
  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <Provider store={store}>
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <MemoryRouter>{children}</MemoryRouter>
      </LocalizationProvider>
    </Provider>
  );

  return {
    ...render(component, { wrapper: Wrapper, ...renderOptions }),
    store,
  };
};

export const mockOptimizationResult = {
  weights: {
    AAPL: 0.3,
    GOOGL: 0.25,
    MSFT: 0.25,
    AMZN: 0.2,
  },
  expected_return: 0.15,
  volatility: 0.18,
  sharpe_ratio: 0.83,
};

export const mockEfficientFrontierData = {
  portfolios: [
    {
      weights: { AAPL: 0.4, GOOGL: 0.3, MSFT: 0.3 },
      expected_return: 0.12,
      volatility: 0.15,
      sharpe_ratio: 0.8,
    },
    {
      weights: { AAPL: 0.3, GOOGL: 0.35, MSFT: 0.35 },
      expected_return: 0.14,
      volatility: 0.17,
      sharpe_ratio: 0.82,
    },
    {
      weights: { AAPL: 0.25, GOOGL: 0.4, MSFT: 0.35 },
      expected_return: 0.16,
      volatility: 0.2,
      sharpe_ratio: 0.8,
    },
  ],
};

export const mockRiskMetricsData = {
  basic_stats: {
    mean: 0.0008,
    std: 0.015,
    skewness: -0.5,
    kurtosis: 3.5,
  },
  var_metrics: {
    historical_var: -0.025,
    parametric_var: -0.024,
    cornish_fisher_var: -0.026,
    monte_carlo_var: -0.025,
    cvar: -0.035,
  },
  drawdown_metrics: {
    max_drawdown: -0.15,
    max_drawdown_duration: 45,
    average_drawdown: -0.05,
    recovery_time: 30,
  },
  performance_ratios: {
    sharpe_ratio: 0.85,
    sortino_ratio: 1.2,
    calmar_ratio: 0.6,
    omega_ratio: 1.5,
    gain_loss_ratio: 1.8,
    profit_factor: 2.1,
    tail_ratio: 1.3,
  },
  relative_metrics: {
    information_ratio: 0.4,
    beta: 1.1,
    alpha: 0.02,
    correlation: 0.85,
    r_squared: 0.72,
  },
};

export const mockMultiStrategyResult = {
  backtest_id: 'test-123',
  status: 'completed',
  total_return: 0.35,
  annual_return: 0.12,
  sharpe_ratio: 0.95,
  max_drawdown: -0.18,
  strategy_weights: {
    'SMA Crossover': 0.5,
    'RSI Mean Reversion': 0.5,
  },
  equity_curve: [
    { timestamp: '2023-01-01', value: 100000 },
    { timestamp: '2023-06-01', value: 115000 },
    { timestamp: '2023-12-01', value: 135000 },
  ],
  metrics: {
    win_rate: 0.58,
    profit_factor: 2.3,
    average_win: 1200,
    average_loss: -800,
  },
};