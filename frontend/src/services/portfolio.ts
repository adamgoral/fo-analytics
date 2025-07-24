import api from './api';
import {
  PortfolioOptimizationRequest,
  PortfolioOptimizationResponse,
  EfficientFrontierRequest,
  EfficientFrontierResponse,
  MultiStrategyBacktestRequest,
  MultiStrategyBacktestResponse,
  RiskMetricsRequest,
  RiskMetricsResponse,
  OptimizationMethodInfo,
} from '../types/portfolio';

class PortfolioService {
  async optimizePortfolio(
    request: PortfolioOptimizationRequest
  ): Promise<PortfolioOptimizationResponse> {
    const response = await api.post('/portfolio/optimize', request);
    return response.data;
  }

  async calculateEfficientFrontier(
    request: EfficientFrontierRequest
  ): Promise<EfficientFrontierResponse> {
    const response = await api.post('/portfolio/efficient-frontier', request);
    return response.data;
  }

  async runMultiStrategyBacktest(
    request: MultiStrategyBacktestRequest
  ): Promise<MultiStrategyBacktestResponse> {
    const response = await api.post('/portfolio/multi-strategy-backtest', request);
    return response.data;
  }

  async calculateRiskMetrics(
    request: RiskMetricsRequest
  ): Promise<RiskMetricsResponse> {
    const response = await api.post('/portfolio/risk-metrics', request);
    return response.data;
  }

  async getOptimizationMethods(): Promise<Record<string, OptimizationMethodInfo>> {
    const response = await api.get('/portfolio/optimization-methods');
    return response.data;
  }
}

export default new PortfolioService();