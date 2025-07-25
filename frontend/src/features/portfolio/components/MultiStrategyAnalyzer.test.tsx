import React from 'react';
import { screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MultiStrategyAnalyzer from './MultiStrategyAnalyzer';
import { renderWithProviders, mockMultiStrategyResult } from '../test-utils';
import portfolioService from '../../../services/portfolio';

// Mock the portfolio service
jest.mock('../../../services/portfolio');
const mockedPortfolioService = portfolioService as jest.Mocked<typeof portfolioService>;

// Mock recharts
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  LineChart: ({ children }: any) => <div data-testid="line-chart">{children}</div>,
  Line: () => <div data-testid="line" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
}));

// Mock EquityChart component
jest.mock('../../../components/Charts/EquityChart', () => ({
  __esModule: true,
  default: ({ data }: any) => <div data-testid="equity-chart">{JSON.stringify(data)}</div>,
}));

describe('MultiStrategyAnalyzer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders strategy configuration section', () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    expect(screen.getByText('Strategy Configuration')).toBeInTheDocument();
  });

  it('displays default strategies', () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    expect(screen.getByText('SMA Crossover')).toBeInTheDocument();
    expect(screen.getByText('RSI Mean Reversion')).toBeInTheDocument();
  });

  it('shows strategy weights', () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    const weightChips = screen.getAllByText(/50\.00%/);
    expect(weightChips.length).toBe(2); // Two default strategies with 50% each
  });

  it('adds new strategy when button clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    const addButton = screen.getByRole('button', { name: /add strategy/i });
    await user.click(addButton);
    
    // Should now have 3 strategies
    const accordions = screen.getAllByRole('button').filter(btn => 
      btn.getAttribute('aria-expanded') !== null
    );
    expect(accordions.length).toBe(3);
  });

  it('removes strategy when remove button clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    // Find remove button in first strategy
    const removeButtons = screen.getAllByTestId('RemoveIcon');
    await user.click(removeButtons[0].parentElement!);
    
    // Should now have only 1 strategy
    const accordions = screen.getAllByRole('button').filter(btn => 
      btn.getAttribute('aria-expanded') !== null
    );
    expect(accordions.length).toBe(1);
  });

  it('prevents removing last strategy', () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    // Remove first strategy
    const removeButtons = screen.getAllByTestId('RemoveIcon');
    fireEvent.click(removeButtons[0].parentElement!);
    
    // The remaining remove button should be disabled
    const remainingRemoveButton = screen.getByTestId('RemoveIcon').parentElement;
    expect(remainingRemoveButton).toBeDisabled();
  });

  it('updates strategy type', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    // Expand first strategy
    const accordionButtons = screen.getAllByRole('button').filter(btn => 
      btn.getAttribute('aria-expanded') !== null
    );
    await user.click(accordionButtons[0]);
    
    // Find and change strategy type
    const strategySelects = screen.getAllByLabelText('Strategy Type');
    fireEvent.mouseDown(strategySelects[0]);
    
    await waitFor(() => {
      const bollingerOption = screen.getByText('Bollinger Bands');
      fireEvent.click(bollingerOption);
    });
    
    expect(screen.getByText('Bollinger Bands')).toBeInTheDocument();
  });

  it('updates strategy parameters', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    // Expand first strategy
    const accordionButtons = screen.getAllByRole('button').filter(btn => 
      btn.getAttribute('aria-expanded') !== null
    );
    await user.click(accordionButtons[0]);
    
    // Find fast period input
    const fastPeriodInput = screen.getByLabelText('Fast Period');
    await user.clear(fastPeriodInput);
    await user.type(fastPeriodInput, '20');
    
    expect(fastPeriodInput).toHaveValue(20);
  });

  it('updates strategy weight with slider', async () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    // Expand first strategy
    const accordionButtons = screen.getAllByRole('button').filter(btn => 
      btn.getAttribute('aria-expanded') !== null
    );
    fireEvent.click(accordionButtons[0]);
    
    // Find weight slider
    const sliders = screen.getAllByRole('slider');
    fireEvent.change(sliders[0], { target: { value: 0.6 } });
    
    expect(screen.getByText('Weight: 60.00%')).toBeInTheDocument();
  });

  it('shows weight normalization warning', () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    // Expand first strategy and change weight
    const accordionButtons = screen.getAllByRole('button').filter(btn => 
      btn.getAttribute('aria-expanded') !== null
    );
    fireEvent.click(accordionButtons[0]);
    
    const sliders = screen.getAllByRole('slider');
    fireEvent.change(sliders[0], { target: { value: 0.6 } });
    
    // Weights now sum to 110%, should show warning
    expect(screen.getByText('Strategy weights must sum to 100%. Click "Normalize Weights" or adjust manually.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /normalize weights/i })).toBeInTheDocument();
  });

  it('normalizes weights when button clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    // Change weight to create imbalance
    const accordionButtons = screen.getAllByRole('button').filter(btn => 
      btn.getAttribute('aria-expanded') !== null
    );
    fireEvent.click(accordionButtons[0]);
    
    const sliders = screen.getAllByRole('slider');
    fireEvent.change(sliders[0], { target: { value: 0.6 } });
    
    // Click normalize
    const normalizeButton = screen.getByRole('button', { name: /normalize weights/i });
    await user.click(normalizeButton);
    
    // Warning should disappear
    expect(screen.queryByText(/Strategy weights must sum to 100%/)).not.toBeInTheDocument();
  });

  it('displays portfolio settings section', () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    expect(screen.getByText('Portfolio Settings')).toBeInTheDocument();
    expect(screen.getByLabelText('Optimization Method')).toBeInTheDocument();
    expect(screen.getByLabelText('Rebalance Frequency')).toBeInTheDocument();
    expect(screen.getByLabelText('Initial Capital')).toBeInTheDocument();
  });

  it('shows default assets', () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    expect(screen.getByText('SPY')).toBeInTheDocument();
    expect(screen.getByText('QQQ')).toBeInTheDocument();
  });

  it('adds new asset', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    const input = screen.getByPlaceholderText('Add symbol');
    const addButton = screen.getAllByRole('button', { name: /add/i })[1]; // Second add button for assets
    
    await user.type(input, 'AAPL');
    await user.click(addButton);
    
    expect(screen.getByText('AAPL')).toBeInTheDocument();
  });

  it('removes asset when delete clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    const spyChip = screen.getByText('SPY').closest('.MuiChip-root');
    const deleteButton = spyChip?.querySelector('[data-testid="CancelIcon"]');
    
    if (deleteButton) {
      await user.click(deleteButton);
    }
    
    expect(screen.queryByText('SPY')).not.toBeInTheDocument();
  });

  it('updates optimization method', async () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    const methodSelect = screen.getByLabelText('Optimization Method');
    fireEvent.mouseDown(methodSelect);
    
    await waitFor(() => {
      const maxSharpeOption = screen.getByText('Maximum Sharpe Ratio');
      fireEvent.click(maxSharpeOption);
    });
    
    expect(screen.getByText('Maximum Sharpe Ratio')).toBeInTheDocument();
  });

  it('updates rebalance frequency', async () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    const frequencySelect = screen.getByLabelText('Rebalance Frequency');
    fireEvent.mouseDown(frequencySelect);
    
    await waitFor(() => {
      const weeklyOption = screen.getByText('Weekly');
      fireEvent.click(weeklyOption);
    });
    
    expect(screen.getByText('Weekly')).toBeInTheDocument();
  });

  it('updates initial capital', async () => {
    const user = userEvent.setup();
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    const capitalInput = screen.getByLabelText('Initial Capital');
    await user.clear(capitalInput);
    await user.type(capitalInput, '250000');
    
    expect(capitalInput).toHaveValue(250000);
  });

  it('disables run button when no strategies', () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    // Remove both strategies
    const removeButtons = screen.getAllByTestId('RemoveIcon');
    fireEvent.click(removeButtons[0].parentElement!);
    
    const runButton = screen.getByRole('button', { name: /run multi-strategy backtest/i });
    expect(runButton).toBeDisabled();
  });

  it('disables run button when no assets', () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    // Remove all assets
    const assetChips = ['SPY', 'QQQ'].map(symbol => 
      screen.getByText(symbol).closest('.MuiChip-root')
    );
    
    assetChips.forEach(chip => {
      const deleteButton = chip?.querySelector('[data-testid="CancelIcon"]');
      if (deleteButton) {
        fireEvent.click(deleteButton);
      }
    });
    
    const runButton = screen.getByRole('button', { name: /run multi-strategy backtest/i });
    expect(runButton).toBeDisabled();
  });

  it('calls service when run backtest clicked', async () => {
    mockedPortfolioService.runMultiStrategyBacktest.mockResolvedValue(mockMultiStrategyResult);
    
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    const runButton = screen.getByRole('button', { name: /run multi-strategy backtest/i });
    fireEvent.click(runButton);
    
    await waitFor(() => {
      expect(mockedPortfolioService.runMultiStrategyBacktest).toHaveBeenCalled();
    });
  });

  it('shows loading state during backtest', () => {
    renderWithProviders(<MultiStrategyAnalyzer />, {
      initialState: {
        multiStrategyBacktest: {
          result: null,
          loading: true,
          error: null,
        },
      },
    });
    
    expect(screen.getByText('Running Backtest...')).toBeInTheDocument();
  });

  it('displays error message on failure', () => {
    const errorMessage = 'Failed to run backtest';
    renderWithProviders(<MultiStrategyAnalyzer />, {
      initialState: {
        multiStrategyBacktest: {
          result: null,
          loading: false,
          error: errorMessage,
        },
      },
    });
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('shows performance summary with results', () => {
    renderWithProviders(<MultiStrategyAnalyzer />, {
      initialState: {
        multiStrategyBacktest: {
          result: mockMultiStrategyResult,
          loading: false,
          error: null,
        },
      },
    });
    
    expect(screen.getByText('Performance Summary')).toBeInTheDocument();
    expect(screen.getByText('Total Return')).toBeInTheDocument();
    expect(screen.getByText('35.00%')).toBeInTheDocument();
    expect(screen.getByText('Annual Return')).toBeInTheDocument();
    expect(screen.getByText('12.00%')).toBeInTheDocument();
  });

  it('displays strategy weights table', () => {
    renderWithProviders(<MultiStrategyAnalyzer />, {
      initialState: {
        multiStrategyBacktest: {
          result: mockMultiStrategyResult,
          loading: false,
          error: null,
        },
      },
    });
    
    expect(screen.getByText('Strategy Weights')).toBeInTheDocument();
    // Check table content
    const table = screen.getByRole('table');
    expect(within(table).getByText('SMA Crossover')).toBeInTheDocument();
    expect(within(table).getByText('50.00%')).toBeInTheDocument();
  });

  it('shows equity curve chart', () => {
    renderWithProviders(<MultiStrategyAnalyzer />, {
      initialState: {
        multiStrategyBacktest: {
          result: mockMultiStrategyResult,
          loading: false,
          error: null,
        },
      },
    });
    
    expect(screen.getByText('Equity Curve')).toBeInTheDocument();
    expect(screen.getByTestId('equity-chart')).toBeInTheDocument();
  });

  it('displays empty state with configuration prompt', () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    expect(screen.getByText('Configure Your Multi-Strategy Portfolio')).toBeInTheDocument();
    expect(screen.getByText('Add strategies, set parameters, and run a backtest to see results')).toBeInTheDocument();
  });

  it('expands first strategy by default', () => {
    renderWithProviders(<MultiStrategyAnalyzer />);
    
    const firstAccordion = screen.getAllByRole('button').filter(btn => 
      btn.getAttribute('aria-expanded') !== null
    )[0];
    
    expect(firstAccordion).toHaveAttribute('aria-expanded', 'true');
  });
});