import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import PerformanceComparison from '../PerformanceComparison';

// Mock recharts to avoid rendering issues in tests
vi.mock('recharts', () => import('../../../test/mocks/recharts'));

const theme = createTheme();

const mockStrategies = [
  {
    name: 'Strategy A',
    totalReturn: 25.5,
    sharpeRatio: 1.8,
    sortinoRatio: 2.1,
    maxDrawdown: -12.3,
    winRate: 65,
    profitFactor: 1.9,
  },
  {
    name: 'Strategy B',
    totalReturn: 18.2,
    sharpeRatio: 1.5,
    sortinoRatio: 1.7,
    maxDrawdown: -8.7,
    winRate: 72,
    profitFactor: 2.1,
  },
];

describe('PerformanceComparison', () => {
  it('renders with default title', () => {
    render(
      <ThemeProvider theme={theme}>
        <PerformanceComparison strategies={mockStrategies} />
      </ThemeProvider>
    );

    expect(screen.getByText('Strategy Performance Comparison')).toBeInTheDocument();
  });

  it('renders with custom title', () => {
    render(
      <ThemeProvider theme={theme}>
        <PerformanceComparison strategies={mockStrategies} title="My Comparison" />
      </ThemeProvider>
    );

    expect(screen.getByText('My Comparison')).toBeInTheDocument();
  });

  it('displays both chart sections', () => {
    render(
      <ThemeProvider theme={theme}>
        <PerformanceComparison strategies={mockStrategies} />
      </ThemeProvider>
    );

    expect(screen.getByText('Key Metrics Comparison')).toBeInTheDocument();
    expect(screen.getByText('Strategy Profile Comparison')).toBeInTheDocument();
  });

  it('handles empty strategies array', () => {
    render(
      <ThemeProvider theme={theme}>
        <PerformanceComparison strategies={[]} />
      </ThemeProvider>
    );

    expect(screen.getByText('Strategy Performance Comparison')).toBeInTheDocument();
  });

  it('handles single strategy', () => {
    render(
      <ThemeProvider theme={theme}>
        <PerformanceComparison strategies={[mockStrategies[0]]} />
      </ThemeProvider>
    );

    expect(screen.getByText('Key Metrics Comparison')).toBeInTheDocument();
    expect(screen.getByText('Strategy Profile Comparison')).toBeInTheDocument();
  });

  it('renders with custom height', () => {
    const { container } = render(
      <ThemeProvider theme={theme}>
        <PerformanceComparison strategies={mockStrategies} height={500} />
      </ThemeProvider>
    );

    // Check that responsive containers are rendered (our mock renders them as divs with data-testid)
    const responsiveContainers = container.querySelectorAll('[data-testid="responsive-container"]');
    expect(responsiveContainers.length).toBeGreaterThan(0);
  });

  it('handles strategies with extreme values', () => {
    const extremeStrategies = [
      {
        name: 'High Return',
        totalReturn: 150,
        sharpeRatio: 3.5,
        sortinoRatio: 4.2,
        maxDrawdown: -45,
        winRate: 90,
        profitFactor: 5.0,
      },
      {
        name: 'Low Return',
        totalReturn: -25,
        sharpeRatio: -0.5,
        sortinoRatio: -0.3,
        maxDrawdown: -60,
        winRate: 30,
        profitFactor: 0.5,
      },
    ];

    render(
      <ThemeProvider theme={theme}>
        <PerformanceComparison strategies={extremeStrategies} />
      </ThemeProvider>
    );

    expect(screen.getByText('Key Metrics Comparison')).toBeInTheDocument();
    expect(screen.getByText('Strategy Profile Comparison')).toBeInTheDocument();
  });
});