import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import portfolioService from '../services/portfolio';
import type {
  PortfolioOptimizationRequest,
  PortfolioOptimizationResponse,
  EfficientFrontierRequest,
  EfficientFrontierResponse,
  MultiStrategyBacktestRequest,
  MultiStrategyBacktestResponse,
  RiskMetricsRequest,
  RiskMetricsResponse,
  OptimizationMethodInfo,
  PortfolioSummary,
} from '../types/portfolio';

interface PortfolioState {
  // Portfolio optimization
  optimization: {
    result: PortfolioOptimizationResponse | null;
    loading: boolean;
    error: string | null;
  };
  
  // Efficient frontier
  efficientFrontier: {
    data: EfficientFrontierResponse | null;
    loading: boolean;
    error: string | null;
  };
  
  // Multi-strategy backtest
  multiStrategyBacktest: {
    result: MultiStrategyBacktestResponse | null;
    loading: boolean;
    error: string | null;
  };
  
  // Risk metrics
  riskMetrics: {
    data: RiskMetricsResponse | null;
    loading: boolean;
    error: string | null;
  };
  
  // Optimization methods
  optimizationMethods: Record<string, OptimizationMethodInfo> | null;
  
  // Current portfolio
  currentPortfolio: PortfolioSummary | null;
  
  // UI state
  selectedTab: number;
  selectedOptimizationMethod: string;
}

const initialState: PortfolioState = {
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
  optimizationMethods: null,
  currentPortfolio: null,
  selectedTab: 0,
  selectedOptimizationMethod: 'mean_variance',
};

// Async thunks
export const optimizePortfolio = createAsyncThunk(
  'portfolio/optimize',
  async (request: PortfolioOptimizationRequest) => {
    return await portfolioService.optimizePortfolio(request);
  }
);

export const calculateEfficientFrontier = createAsyncThunk(
  'portfolio/efficientFrontier',
  async (request: EfficientFrontierRequest) => {
    return await portfolioService.calculateEfficientFrontier(request);
  }
);

export const runMultiStrategyBacktest = createAsyncThunk(
  'portfolio/multiStrategyBacktest',
  async (request: MultiStrategyBacktestRequest) => {
    return await portfolioService.runMultiStrategyBacktest(request);
  }
);

export const calculateRiskMetrics = createAsyncThunk(
  'portfolio/riskMetrics',
  async (request: RiskMetricsRequest) => {
    return await portfolioService.calculateRiskMetrics(request);
  }
);

export const fetchOptimizationMethods = createAsyncThunk(
  'portfolio/fetchMethods',
  async () => {
    return await portfolioService.getOptimizationMethods();
  }
);

const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    setSelectedTab: (state, action: PayloadAction<number>) => {
      state.selectedTab = action.payload;
    },
    setSelectedOptimizationMethod: (state, action: PayloadAction<string>) => {
      state.selectedOptimizationMethod = action.payload;
    },
    setCurrentPortfolio: (state, action: PayloadAction<PortfolioSummary>) => {
      state.currentPortfolio = action.payload;
    },
    clearOptimizationResult: (state) => {
      state.optimization.result = null;
      state.optimization.error = null;
    },
    clearEfficientFrontier: (state) => {
      state.efficientFrontier.data = null;
      state.efficientFrontier.error = null;
    },
    clearMultiStrategyResult: (state) => {
      state.multiStrategyBacktest.result = null;
      state.multiStrategyBacktest.error = null;
    },
    clearRiskMetrics: (state) => {
      state.riskMetrics.data = null;
      state.riskMetrics.error = null;
    },
  },
  extraReducers: (builder) => {
    // Optimize portfolio
    builder
      .addCase(optimizePortfolio.pending, (state) => {
        state.optimization.loading = true;
        state.optimization.error = null;
      })
      .addCase(optimizePortfolio.fulfilled, (state, action) => {
        state.optimization.loading = false;
        state.optimization.result = action.payload;
      })
      .addCase(optimizePortfolio.rejected, (state, action) => {
        state.optimization.loading = false;
        state.optimization.error = action.error.message || 'Portfolio optimization failed';
      });
    
    // Efficient frontier
    builder
      .addCase(calculateEfficientFrontier.pending, (state) => {
        state.efficientFrontier.loading = true;
        state.efficientFrontier.error = null;
      })
      .addCase(calculateEfficientFrontier.fulfilled, (state, action) => {
        state.efficientFrontier.loading = false;
        state.efficientFrontier.data = action.payload;
      })
      .addCase(calculateEfficientFrontier.rejected, (state, action) => {
        state.efficientFrontier.loading = false;
        state.efficientFrontier.error = action.error.message || 'Efficient frontier calculation failed';
      });
    
    // Multi-strategy backtest
    builder
      .addCase(runMultiStrategyBacktest.pending, (state) => {
        state.multiStrategyBacktest.loading = true;
        state.multiStrategyBacktest.error = null;
      })
      .addCase(runMultiStrategyBacktest.fulfilled, (state, action) => {
        state.multiStrategyBacktest.loading = false;
        state.multiStrategyBacktest.result = action.payload;
      })
      .addCase(runMultiStrategyBacktest.rejected, (state, action) => {
        state.multiStrategyBacktest.loading = false;
        state.multiStrategyBacktest.error = action.error.message || 'Multi-strategy backtest failed';
      });
    
    // Risk metrics
    builder
      .addCase(calculateRiskMetrics.pending, (state) => {
        state.riskMetrics.loading = true;
        state.riskMetrics.error = null;
      })
      .addCase(calculateRiskMetrics.fulfilled, (state, action) => {
        state.riskMetrics.loading = false;
        state.riskMetrics.data = action.payload;
      })
      .addCase(calculateRiskMetrics.rejected, (state, action) => {
        state.riskMetrics.loading = false;
        state.riskMetrics.error = action.error.message || 'Risk metrics calculation failed';
      });
    
    // Optimization methods
    builder
      .addCase(fetchOptimizationMethods.fulfilled, (state, action) => {
        state.optimizationMethods = action.payload;
      });
  },
});

export const {
  setSelectedTab,
  setSelectedOptimizationMethod,
  setCurrentPortfolio,
  clearOptimizationResult,
  clearEfficientFrontier,
  clearMultiStrategyResult,
  clearRiskMetrics,
} = portfolioSlice.actions;

export default portfolioSlice.reducer;