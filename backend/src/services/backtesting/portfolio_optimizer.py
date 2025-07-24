"""Portfolio optimization algorithms for multi-asset backtesting.

This module implements various portfolio optimization techniques including:
- Mean-Variance Optimization (Markowitz)
- Black-Litterman Model
- Risk Parity
- Maximum Sharpe Ratio
- Minimum Volatility
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from scipy.optimize import minimize
from scipy import stats
import structlog

logger = structlog.get_logger(__name__)


class PortfolioOptimizer:
    """Main portfolio optimization class with various optimization methods."""
    
    def __init__(self, returns: pd.DataFrame, risk_free_rate: float = 0.02):
        """Initialize portfolio optimizer.
        
        Args:
            returns: DataFrame of asset returns (dates as index, tickers as columns)
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculations
        """
        self.returns = returns
        self.risk_free_rate = risk_free_rate
        self.mean_returns = returns.mean()
        self.cov_matrix = returns.cov()
        self.n_assets = len(returns.columns)
        self.tickers = list(returns.columns)
        
    def _portfolio_stats(self, weights: np.ndarray) -> Tuple[float, float, float]:
        """Calculate portfolio statistics.
        
        Args:
            weights: Array of portfolio weights
            
        Returns:
            Tuple of (return, volatility, sharpe_ratio)
        """
        portfolio_return = np.sum(self.mean_returns * weights) * 252  # Annualized
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix * 252, weights)))
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_vol
        
        return portfolio_return, portfolio_vol, sharpe_ratio
    
    def _negative_sharpe(self, weights: np.ndarray) -> float:
        """Negative Sharpe ratio for minimization."""
        _, _, sharpe = self._portfolio_stats(weights)
        return -sharpe
    
    def _portfolio_volatility(self, weights: np.ndarray) -> float:
        """Portfolio volatility for minimization."""
        _, vol, _ = self._portfolio_stats(weights)
        return vol
    
    def mean_variance_optimization(
        self,
        target_return: Optional[float] = None,
        constraints: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Perform Markowitz mean-variance optimization.
        
        Args:
            target_return: Target annual return (if None, maximizes Sharpe ratio)
            constraints: Additional constraints for optimization
            
        Returns:
            Dict with optimized weights and portfolio statistics
        """
        # Initial guess (equal weights)
        x0 = np.array([1/self.n_assets] * self.n_assets)
        
        # Constraints
        cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]  # Weights sum to 1
        
        if target_return is not None:
            # Add target return constraint
            cons.append({
                'type': 'eq',
                'fun': lambda w: np.sum(self.mean_returns * w) * 252 - target_return
            })
            objective = self._portfolio_volatility
        else:
            # Maximize Sharpe ratio
            objective = self._negative_sharpe
            
        if constraints:
            cons.extend(constraints)
        
        # Bounds (0 <= weight <= 1 for each asset)
        bounds = tuple((0, 1) for _ in range(self.n_assets))
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=cons,
            options={'disp': False}
        )
        
        if not result.success:
            logger.warning(
                "Optimization failed",
                message=result.message,
                target_return=target_return
            )
            
        weights = result.x
        ret, vol, sharpe = self._portfolio_stats(weights)
        
        return {
            'weights': dict(zip(self.tickers, weights)),
            'annual_return': ret,
            'annual_volatility': vol,
            'sharpe_ratio': sharpe,
            'success': result.success
        }
    
    def minimum_volatility_portfolio(self) -> Dict[str, Any]:
        """Find the minimum volatility portfolio."""
        return self.mean_variance_optimization(target_return=None)
    
    def maximum_sharpe_portfolio(self) -> Dict[str, Any]:
        """Find the maximum Sharpe ratio portfolio."""
        return self.mean_variance_optimization(target_return=None)
    
    def efficient_frontier(self, n_portfolios: int = 50) -> pd.DataFrame:
        """Generate efficient frontier portfolios.
        
        Args:
            n_portfolios: Number of portfolios on the efficient frontier
            
        Returns:
            DataFrame with portfolio weights and statistics
        """
        # Get minimum and maximum possible returns
        min_ret = self.mean_returns.min() * 252
        max_ret = self.mean_returns.max() * 252
        
        # Generate target returns
        target_returns = np.linspace(min_ret, max_ret, n_portfolios)
        
        # Store results
        results = []
        
        for target_ret in target_returns:
            try:
                result = self.mean_variance_optimization(target_return=target_ret)
                if result['success']:
                    result['target_return'] = target_ret
                    results.append(result)
            except:
                continue
                
        return pd.DataFrame(results)
    
    def black_litterman(
        self,
        market_caps: Dict[str, float],
        views: Dict[str, float],
        view_confidence: Dict[str, float],
        tau: float = 0.05
    ) -> Dict[str, Any]:
        """Black-Litterman portfolio optimization.
        
        Args:
            market_caps: Market capitalizations for each asset
            views: Expected returns for specific assets (annual)
            view_confidence: Confidence in each view (0-1)
            tau: Scaling factor for prior covariance
            
        Returns:
            Dict with optimized weights and portfolio statistics
        """
        # Calculate market weights
        total_market_cap = sum(market_caps.values())
        market_weights = np.array([
            market_caps.get(ticker, 0) / total_market_cap 
            for ticker in self.tickers
        ])
        
        # Prior (equilibrium) returns
        lambda_param = (self.mean_returns @ market_weights) / (
            market_weights @ self.cov_matrix @ market_weights
        )
        prior_returns = lambda_param * self.cov_matrix @ market_weights
        
        # View matrix P (which assets views are about)
        P = np.zeros((len(views), self.n_assets))
        Q = np.zeros(len(views))  # View returns
        omega_diag = []  # Uncertainty in views
        
        for i, (ticker, view_return) in enumerate(views.items()):
            if ticker in self.tickers:
                idx = self.tickers.index(ticker)
                P[i, idx] = 1
                Q[i] = view_return / 252  # Convert annual to daily
                # Uncertainty inversely proportional to confidence
                confidence = view_confidence.get(ticker, 0.5)
                omega_diag.append(tau * (1 - confidence))
        
        Omega = np.diag(omega_diag)
        
        # Black-Litterman formula
        M = tau * self.cov_matrix
        posterior_cov = np.linalg.inv(np.linalg.inv(M) + P.T @ np.linalg.inv(Omega) @ P)
        posterior_returns = posterior_cov @ (
            np.linalg.inv(M) @ prior_returns + P.T @ np.linalg.inv(Omega) @ Q
        )
        
        # Update optimizer with posterior estimates
        self.mean_returns = pd.Series(posterior_returns, index=self.tickers)
        self.cov_matrix = posterior_cov + self.cov_matrix
        
        # Optimize using posterior estimates
        result = self.maximum_sharpe_portfolio()
        
        # Add Black-Litterman specific info
        result['posterior_returns'] = dict(zip(self.tickers, posterior_returns * 252))
        result['prior_returns'] = dict(zip(self.tickers, prior_returns * 252))
        
        return result
    
    def risk_parity(self) -> Dict[str, Any]:
        """Risk parity portfolio - equal risk contribution from each asset."""
        
        def risk_contribution(weights: np.ndarray) -> np.ndarray:
            """Calculate risk contribution of each asset."""
            portfolio_vol = np.sqrt(weights @ self.cov_matrix @ weights)
            marginal_contrib = self.cov_matrix @ weights
            contrib = weights * marginal_contrib / portfolio_vol
            return contrib
        
        def risk_parity_objective(weights: np.ndarray) -> float:
            """Objective function for risk parity."""
            contrib = risk_contribution(weights)
            # Want equal contribution from each asset
            target_contrib = 1 / self.n_assets
            return np.sum((contrib - target_contrib) ** 2)
        
        # Initial guess
        x0 = np.array([1/self.n_assets] * self.n_assets)
        
        # Constraints
        cons = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}]
        bounds = tuple((0, 1) for _ in range(self.n_assets))
        
        # Optimize
        result = minimize(
            risk_parity_objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=cons,
            options={'disp': False}
        )
        
        weights = result.x
        ret, vol, sharpe = self._portfolio_stats(weights)
        risk_contribs = risk_contribution(weights)
        
        return {
            'weights': dict(zip(self.tickers, weights)),
            'annual_return': ret,
            'annual_volatility': vol,
            'sharpe_ratio': sharpe,
            'risk_contributions': dict(zip(self.tickers, risk_contribs)),
            'success': result.success
        }
    
    def calculate_portfolio_metrics(
        self,
        weights: Dict[str, float],
        lookback_days: int = 252
    ) -> Dict[str, float]:
        """Calculate comprehensive portfolio metrics.
        
        Args:
            weights: Portfolio weights
            lookback_days: Days to use for calculations
            
        Returns:
            Dict of portfolio metrics
        """
        # Convert weights to array
        w = np.array([weights.get(ticker, 0) for ticker in self.tickers])
        
        # Portfolio returns
        portfolio_returns = self.returns @ w
        
        # Basic stats
        ret, vol, sharpe = self._portfolio_stats(w)
        
        # Additional metrics
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_vol = np.sqrt(252) * downside_returns.std()
        sortino_ratio = (ret - self.risk_free_rate) / downside_vol if downside_vol > 0 else 0
        
        # Maximum drawdown
        cum_returns = (1 + portfolio_returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Value at Risk (VaR) and Conditional VaR
        var_95 = np.percentile(portfolio_returns, 5)
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        
        # Calmar ratio
        calmar_ratio = ret / abs(max_drawdown) if max_drawdown != 0 else 0
        
        return {
            'annual_return': ret,
            'annual_volatility': vol,
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown,
            'var_95': var_95 * np.sqrt(252),  # Annual VaR
            'cvar_95': cvar_95 * np.sqrt(252),  # Annual CVaR
            'calmar_ratio': calmar_ratio,
            'information_ratio': ret / vol  # Simplified, assuming benchmark is risk-free rate
        }