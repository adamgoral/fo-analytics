import React from 'react';
import { screen } from '@testing-library/react';
import PortfolioOverview from './PortfolioOverview';
import { renderWithProviders } from '../test-utils';
import { mockPortfolioData } from '../mockData';

describe('PortfolioOverview', () => {
  it('renders empty state when no portfolio data', () => {
    renderWithProviders(<PortfolioOverview />);
    
    expect(screen.getByText('No portfolio data available')).toBeInTheDocument();
    expect(screen.getByText('Add positions or run portfolio optimization to see results')).toBeInTheDocument();
  });

  it('renders portfolio holdings table with data', () => {
    renderWithProviders(<PortfolioOverview />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    expect(screen.getByText('Portfolio Holdings')).toBeInTheDocument();
    
    // Check table headers
    expect(screen.getByText('Symbol')).toBeInTheDocument();
    expect(screen.getByText('Quantity')).toBeInTheDocument();
    expect(screen.getByText('Current Price')).toBeInTheDocument();
    expect(screen.getByText('Cost Basis')).toBeInTheDocument();
    expect(screen.getByText('Market Value')).toBeInTheDocument();
    expect(screen.getByText('Unrealized P&L')).toBeInTheDocument();
    expect(screen.getByText('Weight')).toBeInTheDocument();
  });

  it('displays individual position data correctly', () => {
    renderWithProviders(<PortfolioOverview />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    // Check first position (AAPL)
    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('1,000')).toBeInTheDocument(); // quantity
    expect(screen.getByText('$185.50')).toBeInTheDocument(); // current price
    expect(screen.getByText('$35,500.00')).toBeInTheDocument(); // unrealized P&L
  });

  it('shows total row with portfolio summary', () => {
    renderWithProviders(<PortfolioOverview />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    expect(screen.getByText('Total')).toBeInTheDocument();
    expect(screen.getByText('$1,000,000.00')).toBeInTheDocument(); // total cost
    expect(screen.getByText('$1,250,000.00')).toBeInTheDocument(); // total value
    expect(screen.getByText('$250,000.00')).toBeInTheDocument(); // total P&L
    expect(screen.getByText('(25.00%)')).toBeInTheDocument(); // total P&L percent
  });

  it('displays asset class chips for positions', () => {
    renderWithProviders(<PortfolioOverview />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    const equityChips = screen.getAllByText('Equity');
    expect(equityChips.length).toBeGreaterThan(0);
    
    expect(screen.getByText('Fixed Income')).toBeInTheDocument();
    expect(screen.getByText('Commodities')).toBeInTheDocument();
    expect(screen.getByText('Cryptocurrency')).toBeInTheDocument();
  });

  it('shows last updated timestamp', () => {
    const testDate = new Date('2024-01-15T10:30:00Z');
    const portfolioWithDate = {
      ...mockPortfolioData,
      last_updated: testDate.toISOString(),
    };

    renderWithProviders(<PortfolioOverview />, {
      initialState: {
        currentPortfolio: portfolioWithDate,
      },
    });

    expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
  });

  it('displays positive P&L with success color', () => {
    renderWithProviders(<PortfolioOverview />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    // AAPL has positive P&L
    const aaplPnl = screen.getByText('$35,500.00');
    expect(aaplPnl).toHaveClass('MuiTypography-colorSuccess');
  });

  it('displays negative P&L with error color', () => {
    renderWithProviders(<PortfolioOverview />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    // TLT has negative P&L
    const tltPnl = screen.getByText('-$2,500.00');
    expect(tltPnl).toHaveClass('MuiTypography-colorError');
  });

  it('shows weight allocation with progress bars', () => {
    renderWithProviders(<PortfolioOverview />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    const progressBars = screen.getAllByRole('progressbar');
    expect(progressBars.length).toBe(mockPortfolioData.positions.length);
  });

  it('displays 100% for total weight', () => {
    renderWithProviders(<PortfolioOverview />, {
      initialState: {
        currentPortfolio: mockPortfolioData,
      },
    });

    expect(screen.getByText('100.00%')).toBeInTheDocument();
  });
});