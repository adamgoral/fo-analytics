"""Strategy implementations for backtesting."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, GOOG


class BaseStrategy(Strategy, ABC):
    """Base class for all trading strategies."""
    
    def __init__(self):
        super().__init__()
        self.parameters = {}
        self.entry_rules = {}
        self.exit_rules = {}
        self.risk_parameters = {}
    
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """Set strategy parameters."""
        self.parameters = parameters
    
    def set_entry_rules(self, entry_rules: Dict[str, Any]) -> None:
        """Set entry rules."""
        self.entry_rules = entry_rules
    
    def set_exit_rules(self, exit_rules: Dict[str, Any]) -> None:
        """Set exit rules."""
        self.exit_rules = exit_rules
    
    def set_risk_parameters(self, risk_parameters: Dict[str, Any]) -> None:
        """Set risk management parameters."""
        self.risk_parameters = risk_parameters
    
    @abstractmethod
    def init(self):
        """Initialize the strategy."""
        pass
    
    @abstractmethod
    def next(self):
        """Define what happens on each bar."""
        pass


class SMACrossoverStrategy(BaseStrategy):
    """Simple Moving Average Crossover Strategy."""
    
    def init(self):
        """Initialize the SMA indicators."""
        # Get parameters with defaults
        self.fast_period = self.parameters.get('fast_period', 10)
        self.slow_period = self.parameters.get('slow_period', 20)
        
        # Calculate indicators
        self.sma_fast = self.I(SMA, self.data.Close, self.fast_period)
        self.sma_slow = self.I(SMA, self.data.Close, self.slow_period)
    
    def next(self):
        """Execute trading logic on each bar."""
        # Entry logic
        if crossover(self.sma_fast, self.sma_slow):
            # Apply position sizing from risk parameters
            position_size = self.risk_parameters.get('position_size', 0.95)
            self.buy(size=position_size)
        
        # Exit logic
        elif crossover(self.sma_slow, self.sma_fast):
            self.position.close()


class RSIMeanReversionStrategy(BaseStrategy):
    """RSI Mean Reversion Strategy."""
    
    def init(self):
        """Initialize RSI indicator."""
        self.rsi_period = self.parameters.get('rsi_period', 14)
        self.oversold_level = self.parameters.get('oversold_level', 30)
        self.overbought_level = self.parameters.get('overbought_level', 70)
        
        # Calculate RSI
        self.rsi = self.I(self._calculate_rsi, self.data.Close, self.rsi_period)
    
    def next(self):
        """Execute trading logic."""
        position_size = self.risk_parameters.get('position_size', 0.95)
        
        # Buy when oversold
        if self.rsi[-1] < self.oversold_level and not self.position:
            self.buy(size=position_size)
        
        # Sell when overbought
        elif self.rsi[-1] > self.overbought_level and self.position:
            self.position.close()
    
    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands Strategy."""
    
    def init(self):
        """Initialize Bollinger Bands."""
        self.bb_period = self.parameters.get('bb_period', 20)
        self.bb_std = self.parameters.get('bb_std', 2)
        
        # Calculate Bollinger Bands
        self.bb_middle = self.I(SMA, self.data.Close, self.bb_period)
        bb_std_val = self.I(self._calculate_std, self.data.Close, self.bb_period)
        self.bb_upper = self.bb_middle + self.bb_std * bb_std_val
        self.bb_lower = self.bb_middle - self.bb_std * bb_std_val
    
    def next(self):
        """Execute trading logic."""
        position_size = self.risk_parameters.get('position_size', 0.95)
        
        # Buy when price touches lower band
        if self.data.Close[-1] <= self.bb_lower[-1] and not self.position:
            self.buy(size=position_size)
        
        # Sell when price touches upper band
        elif self.data.Close[-1] >= self.bb_upper[-1] and self.position:
            self.position.close()
    
    @staticmethod
    def _calculate_std(prices: pd.Series, period: int) -> pd.Series:
        """Calculate rolling standard deviation."""
        return prices.rolling(window=period).std()


class MomentumStrategy(BaseStrategy):
    """Simple Momentum Strategy."""
    
    def init(self):
        """Initialize momentum calculation."""
        self.lookback_period = self.parameters.get('lookback_period', 20)
        self.threshold = self.parameters.get('threshold', 0.05)
        
        # Calculate momentum
        self.momentum = self.I(
            lambda x: (x[-1] - x[0]) / x[0],
            self.data.Close.rolling(self.lookback_period + 1)
        )
    
    def next(self):
        """Execute trading logic."""
        if len(self.data) < self.lookback_period + 1:
            return
            
        position_size = self.risk_parameters.get('position_size', 0.95)
        current_momentum = (self.data.Close[-1] - self.data.Close[-self.lookback_period-1]) / self.data.Close[-self.lookback_period-1]
        
        # Buy on positive momentum
        if current_momentum > self.threshold and not self.position:
            self.buy(size=position_size)
        
        # Sell on negative momentum
        elif current_momentum < -self.threshold and self.position:
            self.position.close()


class CustomStrategy(BaseStrategy):
    """Custom strategy that interprets strategy parameters dynamically."""
    
    def init(self):
        """Initialize based on strategy configuration."""
        # This is a placeholder for more complex custom strategies
        # In a real implementation, this would parse the entry/exit rules
        # and create appropriate indicators
        pass
    
    def next(self):
        """Execute custom trading logic."""
        # Placeholder implementation
        # In reality, this would interpret the entry/exit rules
        # and execute trades accordingly
        if not self.position and len(self.data) > 20:
            if self.data.Close[-1] > self.data.Close[-20]:
                self.buy()
        elif self.position and self.data.Close[-1] < self.data.Close[-2]:
            self.position.close()


class StrategyFactory:
    """Factory for creating strategy instances."""
    
    _strategies: Dict[str, Type[BaseStrategy]] = {
        "sma_crossover": SMACrossoverStrategy,
        "rsi_mean_reversion": RSIMeanReversionStrategy,
        "bollinger_bands": BollingerBandsStrategy,
        "momentum": MomentumStrategy,
        "custom": CustomStrategy
    }
    
    def create_strategy(
        self,
        strategy_type: str,
        parameters: Dict[str, Any],
        entry_rules: Dict[str, Any],
        exit_rules: Dict[str, Any],
        risk_parameters: Dict[str, Any]
    ) -> Type[BaseStrategy]:
        """Create a strategy instance with the given parameters."""
        if strategy_type not in self._strategies:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
        
        # Create a new class that inherits from the base strategy
        strategy_base = self._strategies[strategy_type]
        
        # Create a new class with the parameters baked in
        class ConfiguredStrategy(strategy_base):
            def __init__(self):
                super().__init__()
                self.parameters = parameters
                self.entry_rules = entry_rules
                self.exit_rules = exit_rules
                self.risk_parameters = risk_parameters
        
        return ConfiguredStrategy
    
    def list_available_strategies(self) -> list[str]:
        """List all available strategy types."""
        return list(self._strategies.keys())