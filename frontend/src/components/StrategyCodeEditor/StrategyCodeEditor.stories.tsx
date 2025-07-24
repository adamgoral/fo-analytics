import type { Meta, StoryObj } from '@storybook/react';
import { StrategyCodeEditor } from './StrategyCodeEditor';

const meta = {
  title: 'Components/StrategyCodeEditor',
  component: StrategyCodeEditor,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    code: {
      control: 'text',
      description: 'The code content to display',
    },
    language: {
      control: 'select',
      options: ['python', 'javascript', 'typescript'],
      description: 'Programming language for syntax highlighting',
    },
    readOnly: {
      control: 'boolean',
      description: 'Whether the editor is read-only',
    },
    height: {
      control: 'text',
      description: 'Height of the editor',
    },
    title: {
      control: 'text',
      description: 'Title displayed above the editor',
    },
  },
} satisfies Meta<typeof StrategyCodeEditor>;

export default meta;
type Story = StoryObj<typeof meta>;

const pythonStrategyCode = `import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import talib

def calculate_signals(data: pd.DataFrame) -> pd.Series:
    """
    Calculate trading signals based on moving average crossover strategy.
    
    Args:
        data: DataFrame with OHLCV data
    
    Returns:
        Series with signals: 1 (buy), -1 (sell), 0 (hold)
    """
    # Calculate moving averages
    short_window = 20
    long_window = 50
    
    signals = pd.Series(0, index=data.index)
    
    # Calculate the short and long moving averages
    short_mavg = data['close'].rolling(window=short_window, min_periods=1).mean()
    long_mavg = data['close'].rolling(window=long_window, min_periods=1).mean()
    
    # Generate signals
    signals[short_mavg > long_mavg] = 1.0
    signals[short_mavg <= long_mavg] = -1.0
    
    # Calculate actual trading signals (on crossover)
    trading_signals = signals.diff()
    
    return trading_signals

def apply_risk_management(signals: pd.Series, data: pd.DataFrame) -> pd.Series:
    """
    Apply risk management rules to the signals.
    
    Args:
        signals: Raw trading signals
        data: OHLCV data
    
    Returns:
        Risk-adjusted signals
    """
    # Apply stop loss and take profit logic
    adjusted_signals = signals.copy()
    
    # Example: Don't trade if volatility is too high
    volatility = data['close'].pct_change().rolling(20).std()
    high_volatility_threshold = 0.03
    
    adjusted_signals[volatility > high_volatility_threshold] = 0
    
    return adjusted_signals
`;

const javascriptCode = `// Simple momentum strategy
function calculateSignals(data) {
    const signals = new Array(data.length).fill(0);
    const lookback = 20;
    
    for (let i = lookback; i < data.length; i++) {
        const momentum = (data[i].close - data[i - lookback].close) / data[i - lookback].close;
        
        if (momentum > 0.05) {
            signals[i] = 1; // Buy signal
        } else if (momentum < -0.05) {
            signals[i] = -1; // Sell signal
        }
    }
    
    return signals;
}

module.exports = { calculateSignals };`;

export const Default: Story = {
  args: {
    code: pythonStrategyCode,
    language: 'python',
    title: 'Moving Average Crossover Strategy',
    height: '600px',
    readOnly: false,
  },
};

export const ReadOnly: Story = {
  args: {
    code: pythonStrategyCode,
    language: 'python',
    title: 'Strategy Code (Read Only)',
    height: '500px',
    readOnly: true,
  },
};

export const JavaScript: Story = {
  args: {
    code: javascriptCode,
    language: 'javascript',
    title: 'Momentum Strategy',
    height: '400px',
    readOnly: false,
  },
};

export const WithCallbacks: Story = {
  args: {
    code: pythonStrategyCode,
    language: 'python',
    title: 'Interactive Strategy Editor',
    height: '600px',
    readOnly: false,
    onChange: (value) => console.log('Code changed:', value),
    onSave: (code) => console.log('Save clicked with code:', code),
    onRun: (code) => console.log('Run clicked with code:', code),
  },
};

export const EmptyEditor: Story = {
  args: {
    code: '',
    language: 'python',
    title: 'New Strategy',
    height: '600px',
    readOnly: false,
  },
};

export const CompactView: Story = {
  args: {
    code: `def simple_strategy(data):
    # Buy when RSI < 30, sell when RSI > 70
    return calculate_rsi_signals(data)`,
    language: 'python',
    title: 'RSI Strategy',
    height: '200px',
    readOnly: false,
  },
};