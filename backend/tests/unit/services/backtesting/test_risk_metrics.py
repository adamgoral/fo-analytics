"""Unit tests for risk metrics calculator."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime

from services.backtesting.risk_metrics import RiskMetricsCalculator


class TestRiskMetricsCalculator:
    """Test suite for RiskMetricsCalculator."""
    
    @pytest.fixture
    def sample_returns(self):
        """Generate sample return series for testing."""
        np.random.seed(42)
        # Generate 252 days of returns (1 trading year)
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        
        # Mix of positive and negative returns with realistic distribution
        returns = np.random.normal(0.0005, 0.02, 252)  # 0.05% daily mean, 2% daily vol
        
        # Add some extreme events
        returns[50] = -0.05  # 5% loss
        returns[100] = 0.04  # 4% gain
        returns[200] = -0.03  # 3% loss
        
        return pd.Series(returns, index=dates)
    
    @pytest.fixture
    def benchmark_returns(self):
        """Generate benchmark returns for relative metrics."""
        np.random.seed(43)
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        # Slightly lower volatility benchmark
        returns = np.random.normal(0.0003, 0.015, 252)
        return pd.Series(returns, index=dates)
    
    @pytest.fixture
    def calculator(self, sample_returns):
        """Create RiskMetricsCalculator instance."""
        return RiskMetricsCalculator(sample_returns)
    
    @pytest.fixture
    def calculator_with_benchmark(self, sample_returns, benchmark_returns):
        """Create RiskMetricsCalculator with benchmark."""
        return RiskMetricsCalculator(sample_returns, benchmark_returns)
    
    def test_initialization(self, calculator, sample_returns):
        """Test calculator initialization."""
        assert calculator.returns.equals(sample_returns)
        assert calculator.benchmark_returns is None
        assert calculator.trading_days == 252
    
    def test_basic_statistics(self, calculator):
        """Test basic statistical calculations."""
        stats = calculator.basic_statistics()
        
        # Check all expected fields
        expected_fields = [
            'mean_return_daily', 'mean_return_annual',
            'volatility_daily', 'volatility_annual',
            'skewness', 'kurtosis',
            'downside_deviation', 'upside_deviation'
        ]
        
        for field in expected_fields:
            assert field in stats
            assert isinstance(stats[field], float)
        
        # Validate relationships
        assert abs(stats['mean_return_annual'] - stats['mean_return_daily'] * 252) < 0.0001
        assert abs(stats['volatility_annual'] - stats['volatility_daily'] * np.sqrt(252)) < 0.0001
        assert stats['downside_deviation'] >= 0
        assert stats['upside_deviation'] >= 0
    
    def test_value_at_risk(self, calculator):
        """Test VaR calculations."""
        var_results = calculator.value_at_risk(confidence=0.95)
        
        # Check all VaR methods
        var_methods = [
            'historical', 'parametric', 'cornish_fisher', 'cvar', 'monte_carlo'
        ]
        
        for method in var_methods:
            assert f'{method}_daily' in var_results
            assert f'{method}_annual' in var_results
            assert var_results[f'{method}_daily'] < 0  # VaR is negative (loss)
            assert var_results[f'{method}_annual'] < var_results[f'{method}_daily']  # Annual VaR is larger
        
        # CVaR should be worse than VaR
        assert var_results['cvar_daily'] < var_results['historical_daily']
    
    def test_var_confidence_levels(self, calculator):
        """Test VaR at different confidence levels."""
        var_95 = calculator.value_at_risk(0.95)
        var_99 = calculator.value_at_risk(0.99)
        
        # 99% VaR should be more extreme than 95% VaR
        assert var_99['historical_daily'] < var_95['historical_daily']
        assert var_99['cvar_daily'] < var_95['cvar_daily']
    
    def test_drawdown_analysis(self, calculator):
        """Test drawdown analysis."""
        dd_analysis = calculator.drawdown_analysis()
        
        expected_fields = [
            'max_drawdown', 'max_drawdown_date', 'max_drawdown_duration_days',
            'average_drawdown', 'drawdown_periods', 'average_recovery_days',
            'longest_recovery_days'
        ]
        
        for field in expected_fields:
            assert field in dd_analysis
        
        # Validate drawdown properties
        assert dd_analysis['max_drawdown'] < 0  # Drawdown is negative
        assert dd_analysis['average_drawdown'] <= 0
        assert dd_analysis['drawdown_periods'] >= 0
        assert dd_analysis['max_drawdown_duration_days'] >= 0
    
    def test_advanced_ratios(self, calculator):
        """Test advanced performance ratios."""
        ratios = calculator.advanced_ratios()
        
        expected_fields = [
            'omega_ratio', 'gain_loss_ratio', 'profit_factor',
            'tail_ratio', 'positive_periods', 'negative_periods', 'hit_rate'
        ]
        
        for field in expected_fields:
            assert field in ratios
        
        # Validate ratio properties
        assert ratios['positive_periods'] + ratios['negative_periods'] <= len(calculator.returns)
        assert 0 <= ratios['hit_rate'] <= 1
        assert ratios['omega_ratio'] > 0 or ratios['omega_ratio'] is None
    
    def test_relative_metrics(self, calculator_with_benchmark):
        """Test metrics relative to benchmark."""
        rel_metrics = calculator_with_benchmark.relative_metrics()
        
        expected_fields = [
            'information_ratio', 'beta', 'alpha', 'correlation',
            'tracking_error', 'excess_return_mean', 'excess_return_volatility'
        ]
        
        for field in expected_fields:
            assert field in rel_metrics
            assert isinstance(rel_metrics[field], float)
        
        # Validate correlation range
        assert -1 <= rel_metrics['correlation'] <= 1
        assert rel_metrics['tracking_error'] >= 0
    
    def test_risk_adjusted_metrics(self, calculator):
        """Test risk-adjusted performance metrics."""
        risk_free_rate = 0.02
        metrics = calculator.risk_adjusted_metrics(risk_free_rate)
        
        expected_fields = [
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio',
            'sterling_ratio', 'burke_ratio', 'risk_free_rate'
        ]
        
        for field in expected_fields:
            assert field in metrics
        
        assert metrics['risk_free_rate'] == risk_free_rate
        
        # Sortino should generally be higher than Sharpe (uses downside vol only)
        # This may not always hold for specific return distributions
        assert isinstance(metrics['sharpe_ratio'], float)
        assert isinstance(metrics['sortino_ratio'], float)
    
    def test_calculate_all_metrics(self, calculator_with_benchmark):
        """Test comprehensive metric calculation."""
        all_metrics = calculator_with_benchmark.calculate_all_metrics(
            confidence_levels=[0.95, 0.99]
        )
        
        # Check main categories are present
        assert 'mean_return_annual' in all_metrics  # Basic stats
        assert 'var_95' in all_metrics  # VaR results
        assert 'var_99' in all_metrics  # Multiple confidence levels
        assert 'max_drawdown' in all_metrics  # Drawdown analysis
        assert 'omega_ratio' in all_metrics  # Advanced ratios
        assert 'information_ratio' in all_metrics  # Relative metrics
        assert 'sharpe_ratio' in all_metrics  # Risk-adjusted metrics
        
        # Ensure no None values for critical metrics
        critical_metrics = [
            'mean_return_annual', 'volatility_annual', 'max_drawdown',
            'sharpe_ratio', 'sortino_ratio'
        ]
        for metric in critical_metrics:
            assert all_metrics[metric] is not None
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Test with very short return series
        short_returns = pd.Series([0.01, -0.02, 0.015])
        calc = RiskMetricsCalculator(short_returns)
        
        # Should still calculate basic metrics
        stats = calc.basic_statistics()
        assert 'mean_return_daily' in stats
        
        # Test with all positive returns
        positive_returns = pd.Series([0.01, 0.02, 0.015, 0.005, 0.01])
        calc_positive = RiskMetricsCalculator(positive_returns)
        
        dd_analysis = calc_positive.drawdown_analysis()
        assert dd_analysis['max_drawdown'] == 0  # No drawdown
        
        # Test with constant returns
        constant_returns = pd.Series([0.01] * 10)
        calc_constant = RiskMetricsCalculator(constant_returns)
        
        stats = calc_constant.basic_statistics()
        assert stats['volatility_daily'] == 0  # No volatility
    
    def test_tail_ratio(self, calculator):
        """Test tail ratio calculation."""
        # Test with custom percentile
        tail_ratio = calculator._tail_ratio(calculator.returns, percentile=0.05)
        
        assert isinstance(tail_ratio, float)
        # For symmetric distribution, tail ratio should be close to 1
        # For positive skew, > 1; for negative skew, < 1
        assert tail_ratio > 0 or np.isinf(tail_ratio)
    
    def test_omega_ratio(self, calculator):
        """Test omega ratio calculation."""
        returns = calculator.returns
        
        # Test with different thresholds
        omega_0 = calculator._omega_ratio(returns, threshold=0)
        omega_positive = calculator._omega_ratio(returns, threshold=0.001)
        omega_negative = calculator._omega_ratio(returns, threshold=-0.001)
        
        # Higher threshold should result in lower omega ratio
        if not np.isinf(omega_positive) and not np.isinf(omega_negative):
            assert omega_negative > omega_positive