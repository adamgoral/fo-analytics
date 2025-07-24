"""Unit tests for portfolio optimization functionality."""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any

from services.backtesting.portfolio_optimizer import PortfolioOptimizer


class TestPortfolioOptimizer:
    """Test suite for PortfolioOptimizer class."""
    
    @pytest.fixture
    def sample_returns(self):
        """Create sample returns data for testing."""
        # Generate sample returns for 3 assets over 252 days (1 year)
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        
        # Asset 1: High return, high volatility
        asset1_returns = np.random.normal(0.0008, 0.02, 252)
        
        # Asset 2: Medium return, medium volatility
        asset2_returns = np.random.normal(0.0005, 0.015, 252)
        
        # Asset 3: Low return, low volatility (bond-like)
        asset3_returns = np.random.normal(0.0002, 0.008, 252)
        
        returns_df = pd.DataFrame({
            'ASSET1': asset1_returns,
            'ASSET2': asset2_returns,
            'ASSET3': asset3_returns
        }, index=dates)
        
        return returns_df
    
    @pytest.fixture
    def optimizer(self, sample_returns):
        """Create a PortfolioOptimizer instance."""
        return PortfolioOptimizer(sample_returns, risk_free_rate=0.02)
    
    def test_initialization(self, optimizer, sample_returns):
        """Test optimizer initialization."""
        assert optimizer.returns.equals(sample_returns)
        assert optimizer.risk_free_rate == 0.02
        assert optimizer.n_assets == 3
        assert optimizer.tickers == ['ASSET1', 'ASSET2', 'ASSET3']
        assert len(optimizer.mean_returns) == 3
        assert optimizer.cov_matrix.shape == (3, 3)
    
    def test_portfolio_stats(self, optimizer):
        """Test portfolio statistics calculation."""
        # Equal weights
        weights = np.array([1/3, 1/3, 1/3])
        
        ret, vol, sharpe = optimizer._portfolio_stats(weights)
        
        assert isinstance(ret, float)
        assert isinstance(vol, float)
        assert isinstance(sharpe, float)
        assert ret > 0  # Positive return expected
        assert vol > 0  # Positive volatility expected
        assert sharpe != 0  # Non-zero Sharpe ratio
    
    def test_mean_variance_optimization_max_sharpe(self, optimizer):
        """Test mean-variance optimization for maximum Sharpe ratio."""
        result = optimizer.mean_variance_optimization()
        
        assert result['success'] is True
        assert 'weights' in result
        assert len(result['weights']) == 3
        assert abs(sum(result['weights'].values()) - 1.0) < 0.001  # Weights sum to 1
        assert all(0 <= w <= 1 for w in result['weights'].values())  # Valid weight range
        assert result['sharpe_ratio'] > 0
    
    def test_mean_variance_optimization_target_return(self, optimizer):
        """Test mean-variance optimization with target return."""
        target_return = 0.10  # 10% annual return
        result = optimizer.mean_variance_optimization(target_return=target_return)
        
        if result['success']:
            # Check if achieved return is close to target
            assert abs(result['annual_return'] - target_return) < 0.01
            assert abs(sum(result['weights'].values()) - 1.0) < 0.001
    
    def test_minimum_volatility_portfolio(self, optimizer):
        """Test minimum volatility portfolio optimization."""
        result = optimizer.minimum_volatility_portfolio()
        
        assert result['success'] is True
        assert 'weights' in result
        assert result['annual_volatility'] > 0
        
        # Min vol portfolio should have lower vol than equal weight
        equal_weights = np.array([1/3, 1/3, 1/3])
        _, equal_vol, _ = optimizer._portfolio_stats(equal_weights)
        
        # Allow some tolerance due to optimization
        assert result['annual_volatility'] <= equal_vol * 1.01
    
    def test_risk_parity(self, optimizer):
        """Test risk parity portfolio optimization."""
        result = optimizer.risk_parity()
        
        assert result['success'] is True
        assert 'weights' in result
        assert 'risk_contributions' in result
        assert len(result['risk_contributions']) == 3
        
        # Check if risk contributions are roughly equal
        risk_contribs = list(result['risk_contributions'].values())
        target_contrib = 1/3
        for contrib in risk_contribs:
            assert abs(contrib - target_contrib) < 0.1  # 10% tolerance
    
    def test_black_litterman(self, optimizer):
        """Test Black-Litterman optimization."""
        # Market caps (in billions)
        market_caps = {
            'ASSET1': 1000,
            'ASSET2': 800,
            'ASSET3': 500
        }
        
        # Views: ASSET1 will return 15% annually
        views = {'ASSET1': 0.15}
        view_confidence = {'ASSET1': 0.8}
        
        result = optimizer.black_litterman(
            market_caps=market_caps,
            views=views,
            view_confidence=view_confidence,
            tau=0.05
        )
        
        assert 'weights' in result
        assert 'posterior_returns' in result
        assert 'prior_returns' in result
        assert abs(sum(result['weights'].values()) - 1.0) < 0.001
        
        # Asset1 should have higher weight due to positive view
        assert result['weights']['ASSET1'] > 1/3
    
    def test_efficient_frontier(self, optimizer):
        """Test efficient frontier generation."""
        n_portfolios = 10
        frontier = optimizer.efficient_frontier(n_portfolios=n_portfolios)
        
        assert isinstance(frontier, pd.DataFrame)
        assert len(frontier) > 0
        assert len(frontier) <= n_portfolios
        
        # Check required columns
        required_cols = ['weights', 'annual_return', 'annual_volatility', 'sharpe_ratio']
        for col in required_cols:
            assert col in frontier.columns
        
        # Returns should be increasing along frontier
        if len(frontier) > 1:
            returns = frontier['annual_return'].values
            # Allow for some non-monotonicity due to optimization
            assert returns[-1] > returns[0]
    
    def test_calculate_portfolio_metrics(self, optimizer):
        """Test comprehensive portfolio metrics calculation."""
        weights = {'ASSET1': 0.4, 'ASSET2': 0.4, 'ASSET3': 0.2}
        
        metrics = optimizer.calculate_portfolio_metrics(weights, lookback_days=252)
        
        # Check all expected metrics are present
        expected_metrics = [
            'annual_return', 'annual_volatility', 'sharpe_ratio',
            'sortino_ratio', 'max_drawdown', 'var_95', 'cvar_95',
            'calmar_ratio', 'information_ratio'
        ]
        
        for metric in expected_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))
        
        # Validate metric ranges
        assert metrics['annual_volatility'] > 0
        assert metrics['max_drawdown'] < 0  # Drawdown is negative
        assert metrics['var_95'] < 0  # VaR is negative (loss)
        assert metrics['cvar_95'] < 0  # CVaR is negative (loss)
    
    def test_portfolio_with_constraints(self, optimizer):
        """Test optimization with custom constraints."""
        # Constraint: ASSET1 weight must be at least 20%
        constraints = [{
            'type': 'ineq',
            'fun': lambda w: w[0] - 0.2  # w[0] >= 0.2
        }]
        
        result = optimizer.mean_variance_optimization(constraints=constraints)
        
        if result['success']:
            assert result['weights']['ASSET1'] >= 0.2
            assert abs(sum(result['weights'].values()) - 1.0) < 0.001
    
    def test_edge_cases(self, optimizer):
        """Test edge cases and error handling."""
        # Test with single asset (should fail or return trivial solution)
        single_asset_returns = pd.DataFrame({'ASSET1': [0.01, 0.02, -0.01]})
        single_optimizer = PortfolioOptimizer(single_asset_returns)
        
        result = single_optimizer.mean_variance_optimization()
        if result['success']:
            assert result['weights']['ASSET1'] == 1.0
        
        # Test with impossible target return
        impossible_return = 10.0  # 1000% annual return
        result = optimizer.mean_variance_optimization(target_return=impossible_return)
        # Should either fail or return best possible
        assert isinstance(result['success'], bool)