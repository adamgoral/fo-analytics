import React from 'react';
import { screen } from '@testing-library/react';
import AllocationChart from './AllocationChart';
import { renderWithProviders } from '../test-utils';
import { mockPortfolioData } from '../mockData';

// Mock recharts to avoid rendering issues in tests
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />,
  Tooltip: () => <div data-testid="tooltip" />,
}));

describe('AllocationChart', () => {
  it('renders empty state when no allocation data', () => {
    renderWithProviders(<AllocationChart />);
    
    expect(screen.getByText('No allocation data available')).toBeInTheDocument();
  });

  it('displays asset allocation title and chart', () => {
    renderWithProviders(<AllocationChart />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    expect(screen.getByText('Asset Allocation')).toBeInTheDocument();
    expect(screen.getByTestId('pie-chart')).toBeInTheDocument();
  });

  it('shows allocation percentages for each asset class', () => {
    renderWithProviders(<AllocationChart />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    // Check for asset class allocations
    expect(screen.getByText(/Equity.*60\.0%/)).toBeInTheDocument();
    expect(screen.getByText(/Fixed Income.*25\.0%/)).toBeInTheDocument();
    expect(screen.getByText(/Commodities.*10\.0%/)).toBeInTheDocument();
    expect(screen.getByText(/Cryptocurrency.*5\.0%/)).toBeInTheDocument();
  });

  it('displays top holdings section', () => {
    renderWithProviders(<AllocationChart />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    expect(screen.getByText('Top Holdings')).toBeInTheDocument();
  });

  it('shows top 10 positions by weight', () => {
    renderWithProviders(<AllocationChart />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    // Check for some of the top holdings
    expect(screen.getByText('AGG')).toBeInTheDocument(); // Highest weight at 20%
    expect(screen.getByText('SPY')).toBeInTheDocument(); // Second highest at 18%
    expect(screen.getByText('MSFT')).toBeInTheDocument();
    expect(screen.getByText('AAPL')).toBeInTheDocument();
  });

  it('displays position weights in top holdings', () => {
    renderWithProviders(<AllocationChart />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    // AGG has 20% weight
    expect(screen.getByText('20.00%')).toBeInTheDocument();
    // SPY has 18% weight
    expect(screen.getByText('18.00%')).toBeInTheDocument();
  });

  it('shows asset class chips for each holding', () => {
    renderWithProviders(<AllocationChart />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    const equityChips = screen.getAllByText('Equity');
    const fixedIncomeChips = screen.getAllByText('Fixed Income');
    
    expect(equityChips.length).toBeGreaterThan(0);
    expect(fixedIncomeChips.length).toBeGreaterThan(0);
  });

  it('indicates when showing subset of holdings', () => {
    // Create portfolio with more than 10 positions
    const manyPositions = {
      ...mockPortfolioData,
      positions: [
        ...mockPortfolioData.positions,
        ...Array(5).fill(null).map((_, i) => ({
          symbol: `TEST${i}`,
          quantity: 100,
          current_price: 50,
          cost_basis: 4500,
          market_value: 5000,
          unrealized_pnl: 500,
          weight: 0.01,
          asset_class: 'Equity',
        })),
      ],
    };

    renderWithProviders(<AllocationChart />, {
      initialState: {
        currentPortfolio: manyPositions,
      },
    });

    expect(screen.getByText(/Showing top 10 of \d+ holdings/)).toBeInTheDocument();
  });

  it('renders allocation legend with colors', () => {
    renderWithProviders(<AllocationChart />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    // Check for color indicators (rendered as colored boxes)
    const colorBoxes = screen.getAllByText('').filter(element => {
      const parent = element.parentElement;
      return parent && parent.style.backgroundColor;
    });
    
    // Should have color boxes for each asset class
    expect(colorBoxes.length).toBeGreaterThanOrEqual(4); // 4 asset classes
  });

  it('handles empty positions array gracefully', () => {
    const emptyPortfolio = {
      ...mockPortfolioData,
      positions: [],
      allocation_by_asset_class: {},
    };

    renderWithProviders(<AllocationChart />, {
      initialState: {
        currentPortfolio: emptyPortfolio,
      },
    });

    expect(screen.getByText('No allocation data available')).toBeInTheDocument();
  });
});