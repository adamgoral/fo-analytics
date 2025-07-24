// Portfolio-related types matching the backend schemas

export interface PortfolioOptimizationRequest {
  symbols: string[];
  start_date: string;
  end_date: string;
  method: OptimizationMethod;
  target_return?: number;
  risk_free_rate?: number;
  views?: MarketView[];
  view_confidences?: number[];
}

export interface PortfolioOptimizationResponse {
  weights: Record<string, number>;
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
}

export interface EfficientFrontierRequest {
  symbols: string[];
  start_date: string;
  end_date: string;
  risk_free_rate?: number;
  n_portfolios?: number;
}

export interface EfficientFrontierResponse {
  portfolios: Array<{
    weights: Record<string, number>;
    expected_return: number;
    volatility: number;
    sharpe_ratio: number;
  }>;
}

export interface MultiStrategyBacktestRequest {
  strategies: Array<{
    strategy_type: string;
    parameters: Record<string, any>;
    weight: number;
  }>;
  symbols: string[];
  start_date: string;
  end_date: string;
  initial_capital?: number;
  optimization_method?: OptimizationMethod;
  rebalance_frequency?: RebalanceFrequency;
}

export interface MultiStrategyBacktestResponse {
  backtest_id: string;
  status: string;
  total_return: number;
  annual_return: number;
  sharpe_ratio: number;
  max_drawdown: number;
  strategy_weights: Record<string, number>;
  equity_curve: Array<{
    timestamp: string;
    value: number;
  }>;
  metrics: Record<string, number>;
}

export interface RiskMetricsRequest {
  returns: number[];
  benchmark_returns?: number[];
  confidence_level?: number;
  risk_free_rate?: number;
}

export interface RiskMetricsResponse {
  basic_stats: {
    mean: number;
    std: number;
    skewness: number;
    kurtosis: number;
  };
  var_metrics: {
    historical_var: number;
    parametric_var: number;
    cornish_fisher_var: number;
    monte_carlo_var: number;
    cvar: number;
  };
  drawdown_metrics: {
    max_drawdown: number;
    max_drawdown_duration: number;
    average_drawdown: number;
    recovery_time: number;
  };
  performance_ratios: {
    sharpe_ratio: number;
    sortino_ratio: number;
    calmar_ratio: number;
    omega_ratio: number;
    gain_loss_ratio: number;
    profit_factor: number;
    tail_ratio: number;
  };
  relative_metrics?: {
    information_ratio: number;
    beta: number;
    alpha: number;
    correlation: number;
    r_squared: number;
  };
}

export interface OptimizationMethodInfo {
  name: string;
  description: string;
  parameters: Array<{
    name: string;
    type: string;
    required: boolean;
    description: string;
  }>;
}

export interface MarketView {
  assets: number[];
  view: number;
}

export type OptimizationMethod = 
  | 'mean_variance'
  | 'max_sharpe'
  | 'min_volatility'
  | 'risk_parity'
  | 'black_litterman';

export type RebalanceFrequency = 
  | 'daily'
  | 'weekly'
  | 'monthly'
  | 'quarterly'
  | 'yearly';

// Portfolio holdings and positions
export interface PortfolioPosition {
  symbol: string;
  quantity: number;
  current_price: number;
  cost_basis: number;
  market_value: number;
  unrealized_pnl: number;
  weight: number;
  asset_class: string;
}

export interface PortfolioSummary {
  total_value: number;
  total_cost: number;
  total_pnl: number;
  total_pnl_percent: number;
  positions: PortfolioPosition[];
  allocation_by_asset_class: Record<string, number>;
  last_updated: string;
}