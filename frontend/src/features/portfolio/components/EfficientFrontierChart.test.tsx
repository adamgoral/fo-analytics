import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EfficientFrontierChart from './EfficientFrontierChart';
import { renderWithProviders, mockEfficientFrontierData } from '../test-utils';
import portfolioService from '../../../services/portfolio';

// Mock the portfolio service
jest.mock('../../../services/portfolio');
const mockedPortfolioService = portfolioService as jest.Mocked<typeof portfolioService>;

// Mock recharts
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  ScatterChart: ({ children, onClick }: any) => (
    <div data-testid="scatter-chart" onClick={onClick}>
      {children}
    </div>
  ),
  Scatter: () => <div data-testid="scatter" />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  ReferenceDot: () => <div data-testid="reference-dot" />,
}));

describe('EfficientFrontierChart', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders configuration panel', () => {
    renderWithProviders(<EfficientFrontierChart />);
    
    expect(screen.getByText('Configuration')).toBeInTheDocument();
    expect(screen.getByLabelText('Start Date')).toBeInTheDocument();
    expect(screen.getByLabelText('End Date')).toBeInTheDocument();
    expect(screen.getByLabelText('Risk-Free Rate')).toBeInTheDocument();
  });

  it('displays number of portfolios slider', () => {
    renderWithProviders(<EfficientFrontierChart />);
    
    expect(screen.getByText(/Number of Portfolios:/)).toBeInTheDocument();
    expect(screen.getByRole('slider')).toBeInTheDocument();
  });

  it('shows default symbols', () => {
    renderWithProviders(<EfficientFrontierChart />);
    
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('GOOGL')).toBeInTheDocument();
    expect(screen.getByText('MSFT')).toBeInTheDocument();
    expect(screen.getByText('AMZN')).toBeInTheDocument();
  });

  it('adds new symbol when add button clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<EfficientFrontierChart />);
    
    const input = screen.getByPlaceholderText('Add symbol');
    const addButton = screen.getByRole('button', { name: /add/i });
    
    await user.type(input, 'TSLA');
    await user.click(addButton);
    
    expect(screen.getByText('TSLA')).toBeInTheDocument();
  });

  it('removes symbol when delete clicked', async () => {
    const user = userEvent.setup();
    renderWithProviders(<EfficientFrontierChart />);
    
    const aaplChip = screen.getByText('AAPL').closest('.MuiChip-root');
    const deleteButton = aaplChip?.querySelector('[data-testid="CancelIcon"]');
    
    if (deleteButton) {
      await user.click(deleteButton);
    }
    
    expect(screen.queryByText('AAPL')).not.toBeInTheDocument();
  });

  it('shows warning when less than 2 assets', () => {
    renderWithProviders(<EfficientFrontierChart />);
    
    // Remove symbols to have less than 2
    const chips = screen.getAllByRole('button').filter(btn => 
      btn.querySelector('[data-testid="CancelIcon"]')
    );
    
    // Remove all but one
    fireEvent.click(chips[0]);
    fireEvent.click(chips[1]);
    fireEvent.click(chips[2]);
    
    expect(screen.getByText('Add at least 2 assets to calculate efficient frontier')).toBeInTheDocument();
  });

  it('disables calculate button with insufficient assets', () => {
    renderWithProviders(<EfficientFrontierChart />);
    
    // Remove all but one symbol
    const chips = screen.getAllByRole('button').filter(btn => 
      btn.querySelector('[data-testid="CancelIcon"]')
    );
    
    fireEvent.click(chips[0]);
    fireEvent.click(chips[1]);
    fireEvent.click(chips[2]);
    
    const calculateButton = screen.getByRole('button', { name: /calculate frontier/i });
    expect(calculateButton).toBeDisabled();
  });

  it('updates number of portfolios with slider', async () => {
    const user = userEvent.setup();
    renderWithProviders(<EfficientFrontierChart />);
    
    const slider = screen.getByRole('slider');
    
    // Simulate slider change
    fireEvent.change(slider, { target: { value: 80 } });
    
    expect(screen.getByText('Number of Portfolios: 80')).toBeInTheDocument();
  });

  it('calls service when calculate clicked', async () => {
    mockedPortfolioService.calculateEfficientFrontier.mockResolvedValue(mockEfficientFrontierData);
    
    renderWithProviders(<EfficientFrontierChart />);
    
    const calculateButton = screen.getByRole('button', { name: /calculate frontier/i });
    fireEvent.click(calculateButton);
    
    await waitFor(() => {
      expect(mockedPortfolioService.calculateEfficientFrontier).toHaveBeenCalled();
    });
  });

  it('displays loading state during calculation', () => {
    renderWithProviders(<EfficientFrontierChart />, {
      initialState: {
        efficientFrontier: {
          data: null,
          loading: true,
          error: null,
        },
      },
    });
    
    expect(screen.getByText('Calculating...')).toBeInTheDocument();
  });

  it('shows error message on failure', () => {
    const errorMessage = 'Failed to calculate efficient frontier';
    renderWithProviders(<EfficientFrontierChart />, {
      initialState: {
        efficientFrontier: {
          data: null,
          loading: false,
          error: errorMessage,
        },
      },
    });
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('displays chart when data available', () => {
    renderWithProviders(<EfficientFrontierChart />, {
      initialState: {
        efficientFrontier: {
          data: mockEfficientFrontierData,
          loading: false,
          error: null,
        },
      },
    });
    
    expect(screen.getByText('Efficient Frontier')).toBeInTheDocument();
    expect(screen.getByTestId('scatter-chart')).toBeInTheDocument();
  });

  it('shows placeholder when no data', () => {
    renderWithProviders(<EfficientFrontierChart />);
    
    expect(screen.getByText('Configure settings and click "Calculate Frontier" to visualize the efficient frontier')).toBeInTheDocument();
  });

  it('displays selected portfolio details', () => {
    renderWithProviders(<EfficientFrontierChart />, {
      initialState: {
        efficientFrontier: {
          data: mockEfficientFrontierData,
          loading: false,
          error: null,
        },
      },
    });
    
    // Simulate portfolio selection
    const chart = screen.getByTestId('scatter-chart');
    fireEvent.click(chart, {
      activePayload: [{ payload: { index: 0 } }],
    });
    
    // Should show selected portfolio panel
    expect(screen.getByText('Selected Portfolio')).toBeInTheDocument();
  });

  it('shows portfolio metrics when selected', () => {
    // Set up with pre-selected portfolio
    const { rerender } = renderWithProviders(<EfficientFrontierChart />);
    
    // First render with data
    rerender(
      <Provider store={createMockStore({
        efficientFrontier: {
          data: mockEfficientFrontierData,
          loading: false,
          error: null,
        },
      })}>
        <MemoryRouter>
          <EfficientFrontierChart />
        </MemoryRouter>
      </Provider>
    );
    
    // Select first portfolio
    const chart = screen.getByTestId('scatter-chart');
    fireEvent.click(chart, {
      activePayload: [{ payload: { index: 0 } }],
    });
    
    // Check for portfolio details
    expect(screen.getByText('Expected Return')).toBeInTheDocument();
    expect(screen.getByText('12.00%')).toBeInTheDocument();
    expect(screen.getByText('Volatility')).toBeInTheDocument();
    expect(screen.getByText('15.00%')).toBeInTheDocument();
  });

  it('displays portfolio weights for selected', () => {
    renderWithProviders(<EfficientFrontierChart />, {
      initialState: {
        efficientFrontier: {
          data: mockEfficientFrontierData,
          loading: false,
          error: null,
        },
      },
    });
    
    // Simulate selection
    const chart = screen.getByTestId('scatter-chart');
    fireEvent.click(chart, {
      activePayload: [{ payload: { index: 0 } }],
    });
    
    // Check weights section
    expect(screen.getByText('Weights')).toBeInTheDocument();
    expect(screen.getByText('40.00%')).toBeInTheDocument(); // AAPL weight
  });

  it('updates risk-free rate', async () => {
    const user = userEvent.setup();
    renderWithProviders(<EfficientFrontierChart />);
    
    const riskFreeInput = screen.getByLabelText('Risk-Free Rate');
    
    await user.clear(riskFreeInput);
    await user.type(riskFreeInput, '3.5');
    
    expect(riskFreeInput).toHaveValue(3.5);
  });

  it('maintains uppercase for symbol input', async () => {
    const user = userEvent.setup();
    renderWithProviders(<EfficientFrontierChart />);
    
    const input = screen.getByPlaceholderText('Add symbol');
    
    await user.type(input, 'tsla');
    
    expect(input).toHaveValue('TSLA');
  });

  it('clears input after adding symbol', async () => {
    const user = userEvent.setup();
    renderWithProviders(<EfficientFrontierChart />);
    
    const input = screen.getByPlaceholderText('Add symbol');
    const addButton = screen.getByRole('button', { name: /add/i });
    
    await user.type(input, 'TSLA');
    await user.click(addButton);
    
    expect(input).toHaveValue('');
  });
});