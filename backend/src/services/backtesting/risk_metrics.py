"""Advanced risk metrics calculation for backtesting results.

This module provides comprehensive risk analysis including:
- Value at Risk (VaR) - Historical, Parametric, Monte Carlo
- Conditional Value at Risk (CVaR/ES)
- Information Ratio
- Omega Ratio
- Kurtosis and Skewness
- Maximum Drawdown Duration
- Recovery Time Analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from scipy import stats
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


class RiskMetricsCalculator:
    """Calculator for advanced risk metrics."""
    
    def __init__(self, returns: Union[pd.Series, np.ndarray], benchmark_returns: Optional[pd.Series] = None):
        """Initialize risk metrics calculator.
        
        Args:
            returns: Series or array of returns (daily)
            benchmark_returns: Optional benchmark returns for relative metrics
        """
        self.returns = pd.Series(returns) if isinstance(returns, np.ndarray) else returns
        self.benchmark_returns = benchmark_returns
        self.trading_days = 252  # Annual trading days
        
    def calculate_all_metrics(self, confidence_levels: List[float] = [0.95, 0.99]) -> Dict[str, Any]:
        """Calculate all available risk metrics.
        
        Args:
            confidence_levels: Confidence levels for VaR/CVaR calculations
            
        Returns:
            Dict containing all calculated metrics
        """
        metrics = {}
        
        # Basic statistics
        metrics.update(self.basic_statistics())
        
        # VaR and CVaR
        for confidence in confidence_levels:
            var_metrics = self.value_at_risk(confidence)
            metrics[f'var_{int(confidence*100)}'] = var_metrics
            
        # Drawdown analysis
        metrics.update(self.drawdown_analysis())
        
        # Advanced ratios
        metrics.update(self.advanced_ratios())
        
        # Relative metrics if benchmark provided
        if self.benchmark_returns is not None:
            metrics.update(self.relative_metrics())
            
        # Risk-adjusted metrics
        metrics.update(self.risk_adjusted_metrics())
        
        return metrics
        
    def basic_statistics(self) -> Dict[str, float]:
        """Calculate basic statistical measures."""
        daily_returns = self.returns.dropna()
        
        return {
            'mean_return_daily': float(daily_returns.mean()),
            'mean_return_annual': float(daily_returns.mean() * self.trading_days),
            'volatility_daily': float(daily_returns.std()),
            'volatility_annual': float(daily_returns.std() * np.sqrt(self.trading_days)),
            'skewness': float(stats.skew(daily_returns)),
            'kurtosis': float(stats.kurtosis(daily_returns)),
            'downside_deviation': float(self._downside_deviation()),
            'upside_deviation': float(self._upside_deviation())
        }
        
    def value_at_risk(self, confidence: float = 0.95) -> Dict[str, float]:
        """Calculate Value at Risk using multiple methods.
        
        Args:
            confidence: Confidence level (e.g., 0.95 for 95%)
            
        Returns:
            Dict with VaR calculations using different methods
        """
        daily_returns = self.returns.dropna()
        
        # Historical VaR
        historical_var = self._historical_var(daily_returns, confidence)
        
        # Parametric VaR (assumes normal distribution)
        parametric_var = self._parametric_var(daily_returns, confidence)
        
        # Cornish-Fisher VaR (adjusts for skewness and kurtosis)
        cf_var = self._cornish_fisher_var(daily_returns, confidence)
        
        # CVaR (Conditional VaR / Expected Shortfall)
        cvar = self._conditional_var(daily_returns, confidence)
        
        # Monte Carlo VaR
        mc_var = self._monte_carlo_var(daily_returns, confidence)
        
        return {
            'historical_daily': float(historical_var),
            'historical_annual': float(historical_var * np.sqrt(self.trading_days)),
            'parametric_daily': float(parametric_var),
            'parametric_annual': float(parametric_var * np.sqrt(self.trading_days)),
            'cornish_fisher_daily': float(cf_var),
            'cornish_fisher_annual': float(cf_var * np.sqrt(self.trading_days)),
            'cvar_daily': float(cvar),
            'cvar_annual': float(cvar * np.sqrt(self.trading_days)),
            'monte_carlo_daily': float(mc_var),
            'monte_carlo_annual': float(mc_var * np.sqrt(self.trading_days))
        }
        
    def _historical_var(self, returns: pd.Series, confidence: float) -> float:
        """Calculate historical VaR."""
        return np.percentile(returns, (1 - confidence) * 100)
        
    def _parametric_var(self, returns: pd.Series, confidence: float) -> float:
        """Calculate parametric VaR assuming normal distribution."""
        mean = returns.mean()
        std = returns.std()
        z_score = stats.norm.ppf(1 - confidence)
        return mean + z_score * std
        
    def _cornish_fisher_var(self, returns: pd.Series, confidence: float) -> float:
        """Calculate Cornish-Fisher VaR adjusting for higher moments."""
        mean = returns.mean()
        std = returns.std()
        skew = stats.skew(returns)
        kurt = stats.kurtosis(returns)
        
        z = stats.norm.ppf(1 - confidence)
        cf_z = z + (z**2 - 1) * skew / 6 + (z**3 - 3*z) * kurt / 24 - (2*z**3 - 5*z) * skew**2 / 36
        
        return mean + cf_z * std
        
    def _conditional_var(self, returns: pd.Series, confidence: float) -> float:
        """Calculate Conditional VaR (Expected Shortfall)."""
        var = self._historical_var(returns, confidence)
        return returns[returns <= var].mean()
        
    def _monte_carlo_var(self, returns: pd.Series, confidence: float, n_simulations: int = 10000) -> float:
        """Calculate Monte Carlo VaR."""
        mean = returns.mean()
        std = returns.std()
        
        # Generate simulations
        simulated_returns = np.random.normal(mean, std, n_simulations)
        
        return np.percentile(simulated_returns, (1 - confidence) * 100)
        
    def drawdown_analysis(self) -> Dict[str, Any]:
        """Comprehensive drawdown analysis."""
        cumulative_returns = (1 + self.returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        
        # Find all drawdown periods
        drawdown_periods = self._identify_drawdown_periods(drawdown)
        
        # Maximum drawdown
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()
        
        # Maximum drawdown duration
        max_dd_duration = 0
        current_dd_duration = 0
        recovery_times = []
        
        for period in drawdown_periods:
            duration = (period['end'] - period['start']).days if period['end'] else np.nan
            if not np.isnan(duration):
                recovery_times.append(duration)
                if duration > max_dd_duration:
                    max_dd_duration = duration
                    
        return {
            'max_drawdown': float(max_dd),
            'max_drawdown_date': str(max_dd_idx) if pd.notna(max_dd_idx) else None,
            'max_drawdown_duration_days': int(max_dd_duration),
            'average_drawdown': float(drawdown[drawdown < 0].mean()) if len(drawdown[drawdown < 0]) > 0 else 0,
            'drawdown_periods': len(drawdown_periods),
            'average_recovery_days': float(np.mean(recovery_times)) if recovery_times else 0,
            'longest_recovery_days': int(max(recovery_times)) if recovery_times else 0
        }
        
    def _identify_drawdown_periods(self, drawdown: pd.Series) -> List[Dict]:
        """Identify all drawdown periods."""
        periods = []
        in_drawdown = False
        start_date = None
        
        for date, dd in drawdown.items():
            if dd < 0 and not in_drawdown:
                # Start of drawdown
                in_drawdown = True
                start_date = date
            elif dd >= 0 and in_drawdown:
                # End of drawdown
                in_drawdown = False
                periods.append({
                    'start': start_date,
                    'end': date,
                    'max_drawdown': drawdown[start_date:date].min()
                })
                
        # Handle ongoing drawdown
        if in_drawdown:
            periods.append({
                'start': start_date,
                'end': None,
                'max_drawdown': drawdown[start_date:].min()
            })
            
        return periods
        
    def advanced_ratios(self) -> Dict[str, float]:
        """Calculate advanced performance ratios."""
        returns = self.returns.dropna()
        
        # Omega Ratio
        threshold = 0  # Can be adjusted
        omega = self._omega_ratio(returns, threshold)
        
        # Gain/Loss Ratio
        gains = returns[returns > 0]
        losses = returns[returns < 0]
        gain_loss_ratio = (gains.mean() / abs(losses.mean())) if len(losses) > 0 else np.inf
        
        # Profit Factor
        total_gains = gains.sum()
        total_losses = abs(losses.sum())
        profit_factor = total_gains / total_losses if total_losses > 0 else np.inf
        
        # Tail Ratio
        tail_ratio = self._tail_ratio(returns)
        
        return {
            'omega_ratio': float(omega),
            'gain_loss_ratio': float(gain_loss_ratio) if not np.isinf(gain_loss_ratio) else None,
            'profit_factor': float(profit_factor) if not np.isinf(profit_factor) else None,
            'tail_ratio': float(tail_ratio),
            'positive_periods': int(len(gains)),
            'negative_periods': int(len(losses)),
            'hit_rate': float(len(gains) / len(returns)) if len(returns) > 0 else 0
        }
        
    def _omega_ratio(self, returns: pd.Series, threshold: float = 0) -> float:
        """Calculate Omega Ratio."""
        excess_returns = returns - threshold
        positive_sum = excess_returns[excess_returns > 0].sum()
        negative_sum = abs(excess_returns[excess_returns < 0].sum())
        
        return positive_sum / negative_sum if negative_sum > 0 else np.inf
        
    def _tail_ratio(self, returns: pd.Series, percentile: float = 0.05) -> float:
        """Calculate tail ratio (ratio of right tail to left tail)."""
        right_tail = np.percentile(returns, 100 * (1 - percentile))
        left_tail = abs(np.percentile(returns, 100 * percentile))
        
        return right_tail / left_tail if left_tail > 0 else np.inf
        
    def relative_metrics(self) -> Dict[str, float]:
        """Calculate metrics relative to benchmark."""
        if self.benchmark_returns is None:
            return {}
            
        # Align returns
        aligned_returns, aligned_benchmark = self.returns.align(self.benchmark_returns, join='inner')
        
        # Excess returns
        excess_returns = aligned_returns - aligned_benchmark
        
        # Information Ratio
        tracking_error = excess_returns.std() * np.sqrt(self.trading_days)
        information_ratio = (excess_returns.mean() * self.trading_days) / tracking_error if tracking_error > 0 else 0
        
        # Beta
        covariance = aligned_returns.cov(aligned_benchmark)
        benchmark_variance = aligned_benchmark.var()
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
        
        # Alpha (using CAPM)
        risk_free_rate = 0.02  # Assume 2% risk-free rate
        market_premium = aligned_benchmark.mean() * self.trading_days - risk_free_rate
        expected_return = risk_free_rate + beta * market_premium
        actual_return = aligned_returns.mean() * self.trading_days
        alpha = actual_return - expected_return
        
        # Correlation
        correlation = aligned_returns.corr(aligned_benchmark)
        
        return {
            'information_ratio': float(information_ratio),
            'beta': float(beta),
            'alpha': float(alpha),
            'correlation': float(correlation),
            'tracking_error': float(tracking_error),
            'excess_return_mean': float(excess_returns.mean() * self.trading_days),
            'excess_return_volatility': float(excess_returns.std() * np.sqrt(self.trading_days))
        }
        
    def risk_adjusted_metrics(self, risk_free_rate: float = 0.02) -> Dict[str, float]:
        """Calculate risk-adjusted performance metrics."""
        returns = self.returns.dropna()
        
        # Annualized metrics
        annual_return = returns.mean() * self.trading_days
        annual_vol = returns.std() * np.sqrt(self.trading_days)
        
        # Sharpe Ratio
        sharpe = (annual_return - risk_free_rate) / annual_vol if annual_vol > 0 else 0
        
        # Sortino Ratio
        downside_vol = self._downside_deviation() * np.sqrt(self.trading_days)
        sortino = (annual_return - risk_free_rate) / downside_vol if downside_vol > 0 else 0
        
        # Calmar Ratio
        max_dd = self.drawdown_analysis()['max_drawdown']
        calmar = annual_return / abs(max_dd) if max_dd != 0 else 0
        
        # Sterling Ratio
        avg_dd = self.drawdown_analysis()['average_drawdown']
        sterling = annual_return / abs(avg_dd) if avg_dd != 0 else 0
        
        # Burke Ratio (uses square root of sum of squared drawdowns)
        drawdowns = self._get_drawdown_series()
        burke_denominator = np.sqrt((drawdowns**2).sum())
        burke = annual_return / burke_denominator if burke_denominator > 0 else 0
        
        return {
            'sharpe_ratio': float(sharpe),
            'sortino_ratio': float(sortino),
            'calmar_ratio': float(calmar),
            'sterling_ratio': float(sterling),
            'burke_ratio': float(burke),
            'risk_free_rate': risk_free_rate
        }
        
    def _downside_deviation(self, target: float = 0) -> float:
        """Calculate downside deviation."""
        downside_returns = self.returns[self.returns < target]
        return downside_returns.std() if len(downside_returns) > 0 else 0
        
    def _upside_deviation(self, target: float = 0) -> float:
        """Calculate upside deviation."""
        upside_returns = self.returns[self.returns > target]
        return upside_returns.std() if len(upside_returns) > 0 else 0
        
    def _get_drawdown_series(self) -> pd.Series:
        """Get drawdown series."""
        cumulative_returns = (1 + self.returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        return (cumulative_returns - running_max) / running_max