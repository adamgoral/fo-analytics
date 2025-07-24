import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PortfolioOptimizer from './PortfolioOptimizer';
import { renderWithProviders, mockOptimizationResult } from '../test-utils';
import portfolioService from '../../../services/portfolio';

// Mock the portfolio service
jest.mock('../../../services/portfolio');
const mockedPortfolioService = portfolioService as jest.Mocked<typeof portfolioService>;

describe('PortfolioOptimizer', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders optimization settings section', () => {
    renderWithProviders(<PortfolioOptimizer />);
    
    expect(screen.getByText('Optimization Settings')).toBeInTheDocument();
    expect(screen.getByLabelText('Optimization Method')).toBeInTheDocument();
    expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
    expect(screen.getByLabelText('End Date')).toBeInTheDocument();
  });

  it('displays optimization methods in dropdown', async () => {
    renderWithProviders(<PortfolioOptimizer />);
    
    const methodSelect = screen.getByLabelText('Optimization Method');
    fireEvent.mouseDown(methodSelect);
    
    await waitFor(() => {
      expect(screen.getByText('Mean-Variance Optimization')).toBeInTheDocument();
      expect(screen.getByText('Maximum Sharpe Ratio')).toBeInTheDocument();
    });
  });

  it('shows target return field for mean variance method', () => {
    renderWithProviders(<PortfolioOptimizer />, {
      initialState: {
        selectedOptimizationMethod: 'mean_variance',
      },
    });
    
    expect(screen.getByLabelText('Target Return')).toBeInTheDocument();
  });

  it('shows risk-free rate field for sharpe ratio methods', () => {
    renderWithProviders(<PortfolioOptimizer />, {
      initialState: {
        selectedOptimizationMethod: 'max_sharpe',
      },
    });
    
    expect(screen.getByLabelText('Risk-Free Rate')).toBeInTheDocument();
  });

  it('displays default symbols', () => {
    renderWithProviders(<PortfolioOptimizer />);
    
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('GOOGL')).toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
  });

  it('adds new symbol when Add button clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioOptimizer />);
    
    const input = screen.getByPlaceholderText('Add symbol');
    const addButton = screen.getByRole('button', { name: /add/i });
    
    await user.type(input, 'TSLA');
    await user.click(addButton);
    
    expect(screen.getByText('TSLA')).toBeInTheDocument();
  });

  it('removes symbol when delete icon clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioOptimizer />);
    
    // Find and click the delete button for AAPL
    const aaplChip = screen.getByText('AAPL').closest('.MuiChip-root');
    const deleteButton = aaplChip?.querySelector('[data-testid="CancelIcon"]');
    
    if (deleteButton) {
      await user.click(deleteButton);
    }
    
    expect(screen.queryByText('AAPL')).not.toBeInTheDocument();
  });

  it('shows warning when less than 2 assets', () => {
    renderWithProviders(<PortfolioOptimizer />);
    
    // Remove symbols to have less than 2
    const chips = screen.getAllByRole('button').filter(btn => 
      btn.querySelector('[data-testid="CancelIcon"]')
    );
    
    // Click delete on first two chips
    fireEvent.click(chips[0]);
    fireEvent.click(chips[1]);
    
    expect(screen.getByText('Add at least 2 assets to run optimization')).toBeInTheDocument();
  });

  it('disables optimize button with less than 2 assets', () => {
    renderWithProviders(<PortfolioOptimizer />);
    
    // Remove all but one symbol
    const chips = screen.getAllByRole('button').filter(btn => 
      btn.querySelector('[data-testid="CancelIcon"]')
    );
    
    fireEvent.click(chips[0]);
    fireEvent.click(chips[1]);
    
    const optimizeButton = screen.getByRole('button', { name: /optimize portfolio/i });
    expect(optimizeButton).toBeDisabled();
  });

  it('calls optimization service when optimize clicked', async () => {
    mockedPortfolioService.optimizePortfolio.mockResolvedValue(mockOptimizationResult);
    
    renderWithProviders(<PortfolioOptimizer />);
    
    const optimizeButton = screen.getByRole('button', { name: /optimize portfolio/i });
    fireEvent.click(optimizeButton);
    
    await waitFor(() => {
      expect(mockedPortfolioService.optimizePortfolio).toHaveBeenCalled();
    });
  });

  it('displays optimization results', async () => {
    renderWithProviders(<PortfolioOptimizer />, {
      initialState: {
        optimization: {
          result: mockOptimizationResult,
          loading: false,
          error: null,
        },
      },
    });
    
    expect(screen.getByText('Optimization Results')).toBeInTheDocument();
    expect(screen.getByText('Expected Return')).toBeInTheDocument();
    expect(screen.getByText('15.00%')).toBeInTheDocument();
    expect(screen.getByText('Volatility')).toBeInTheDocument();
    expect(screen.getByText('18.00%')).toBeInTheDocument();
    expect(screen.getByText('Sharpe Ratio')).toBeInTheDocument();
    expect(screen.getByText('0.830')).toBeInTheDocument();
  });

  it('shows optimal weights table', () => {
    renderWithProviders(<PortfolioOptimizer />, {
      initialState: {
        optimization: {
          result: mockOptimizationResult,
          loading: false,
          error: null,
        },
      },
    });
    
    expect(screen.getByText('Optimal Weights')).toBeInTheDocument();
    expect(screen.getByText('30.00%')).toBeInTheDocument(); // AAPL weight
    expect(screen.getByText('25.00%')).toBeInTheDocument(); // GOOGL weight
  });

  it('displays loading state during optimization', () => {
    renderWithProviders(<PortfolioOptimizer />, {
      initialState: {
        optimization: {
          result: null,
          loading: true,
          error: null,
        },
      },
    });
    
    expect(screen.getByText('Optimizing...')).toBeInTheDocument();
  });

  it('shows error message on optimization failure', () => {
    const errorMessage = 'Failed to optimize portfolio';
    renderWithProviders(<PortfolioOptimizer />, {
      initialState: {
        optimization: {
          result: null,
          loading: false,
          error: errorMessage,
        },
      },
    });
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('displays apply to portfolio button with results', () => {
    renderWithProviders(<PortfolioOptimizer />, {
      initialState: {
        optimization: {
          result: mockOptimizationResult,
          loading: false,
          error: null,
        },
      },
    });
    
    expect(screen.getByRole('button', { name: /apply to portfolio/i })).toBeInTheDocument();
  });

  it('converts symbol input to uppercase', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioOptimizer />);
    
    const input = screen.getByPlaceholderText('Add symbol');
    await user.type(input, 'tsla');
    
    expect(input).toHaveValue('TSLA');
  });

  it('prevents duplicate symbols', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioOptimizer />);
    
    const input = screen.getByPlaceholderText('Add symbol');
    const addButton = screen.getByRole('button', { name: /add/i });
    
    // Try to add existing symbol
    await user.type(input, 'AAPL');
    await user.click(addButton);
    
    // Should still only have one AAPL
    const aaplElements = screen.getAllByText('AAPL');
    expect(aaplElements).toHaveLength(1);
  });

  it('adds symbol on Enter key press', async () => {
    const user = userEvent.setup();
    renderWithProviders(<PortfolioOptimizer />);
    
    const input = screen.getByPlaceholderText('Add symbol');
    
    await user.type(input, 'TSLA{enter}');
    
    expect(screen.getByText('TSLA')).toBeInTheDocument();
    expect(input).toHaveValue(''); // Input should be cleared
  });
});