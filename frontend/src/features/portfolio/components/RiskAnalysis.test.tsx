import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import RiskAnalysis from './RiskAnalysis';
import { renderWithProviders, mockRiskMetricsData } from '../test-utils';

describe('RiskAnalysis', () => {
  it('renders empty state when no risk metrics data', () => {
    renderWithProviders(<RiskAnalysis />);
    
    expect(screen.getByText('No risk analysis data available')).toBeInTheDocument();
    expect(screen.getByText('Run portfolio optimization or load historical data to see risk metrics')).toBeInTheDocument();
  });

  it('displays risk summary cards with data', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    expect(screen.getByText('Value at Risk (95%)')).toBeInTheDocument();
    expect(screen.getAllByText('-2.50%')[0]).toBeInTheDocument(); // VaR value
    
    expect(screen.getByText('Max Drawdown')).toBeInTheDocument();
    expect(screen.getByText('-15.00%')).toBeInTheDocument(); // Drawdown value
    
    expect(screen.getByText('Sharpe Ratio')).toBeInTheDocument();
    expect(screen.getByText('0.850')).toBeInTheDocument(); // Sharpe value
    
    expect(screen.getByText('Volatility')).toBeInTheDocument();
    expect(screen.getByText('1.50%')).toBeInTheDocument(); // Volatility value
  });

  it('shows risk level chips with appropriate colors', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    // Check for risk level chips
    const riskChips = screen.getAllByText(/LOW|MEDIUM|HIGH/);
    expect(riskChips.length).toBeGreaterThan(0);
  });

  it('displays drawdown duration', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    expect(screen.getByText('Duration: 45 days')).toBeInTheDocument();
  });

  it('renders all tab options', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    expect(screen.getByText('VaR Analysis')).toBeInTheDocument();
    expect(screen.getByText('Drawdown Analysis')).toBeInTheDocument();
    expect(screen.getByText('Performance Ratios')).toBeInTheDocument();
    expect(screen.getByText('Statistical Measures')).toBeInTheDocument();
    expect(screen.getByText('Relative Metrics')).toBeInTheDocument();
  });

  it('switches tabs when clicked', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    const performanceTab = screen.getByText('Performance Ratios');
    fireEvent.click(performanceTab);
    
    // Should show performance ratios content
    expect(screen.getByText('Risk-adjusted returns (higher is better)')).toBeInTheDocument();
  });

  it('displays VaR metrics in VaR tab', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    expect(screen.getByText('Value at Risk (VaR) Metrics')).toBeInTheDocument();
    expect(screen.getByText('Historical VaR')).toBeInTheDocument();
    expect(screen.getByText('Parametric VaR')).toBeInTheDocument();
    expect(screen.getByText('Cornish-Fisher VaR')).toBeInTheDocument();
    expect(screen.getByText('Monte Carlo VaR')).toBeInTheDocument();
    expect(screen.getByText('Conditional VaR (CVaR)')).toBeInTheDocument();
  });

  it('shows VaR explanation info box', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    expect(screen.getByText('Understanding VaR')).toBeInTheDocument();
    expect(screen.getByText(/VaR represents the maximum loss expected/)).toBeInTheDocument();
  });

  it('displays drawdown metrics in drawdown tab', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    const drawdownTab = screen.getByText('Drawdown Analysis');
    fireEvent.click(drawdownTab);

    expect(screen.getByText('Drawdown Metrics')).toBeInTheDocument();
    expect(screen.getByText('Maximum Drawdown')).toBeInTheDocument();
    expect(screen.getByText('Max Drawdown Duration')).toBeInTheDocument();
    expect(screen.getByText('Average Drawdown')).toBeInTheDocument();
    expect(screen.getByText('Recovery Time')).toBeInTheDocument();
  });

  it('shows drawdown risk assessment with progress bar', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    const drawdownTab = screen.getByText('Drawdown Analysis');
    fireEvent.click(drawdownTab);

    expect(screen.getByText('Drawdown Risk Assessment')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('displays all performance ratios', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    const ratiosTab = screen.getByText('Performance Ratios');
    fireEvent.click(ratiosTab);

    expect(screen.getByText('Sortino Ratio')).toBeInTheDocument();
    expect(screen.getByText('Calmar Ratio')).toBeInTheDocument();
    expect(screen.getByText('Omega Ratio')).toBeInTheDocument();
    expect(screen.getByText('Gain/Loss Ratio')).toBeInTheDocument();
    expect(screen.getByText('Profit Factor')).toBeInTheDocument();
    expect(screen.getByText('Tail Ratio')).toBeInTheDocument();
  });

  it('shows ratio descriptions', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    const ratiosTab = screen.getByText('Performance Ratios');
    fireEvent.click(ratiosTab);

    expect(screen.getByText('Downside risk-adjusted returns')).toBeInTheDocument();
    expect(screen.getByText('Return vs max drawdown')).toBeInTheDocument();
  });

  it('displays statistical measures', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    const statsTab = screen.getByText('Statistical Measures');
    fireEvent.click(statsTab);

    expect(screen.getByText('Mean Return')).toBeInTheDocument();
    expect(screen.getByText('Standard Deviation')).toBeInTheDocument();
    expect(screen.getByText('Skewness')).toBeInTheDocument();
    expect(screen.getByText('Kurtosis')).toBeInTheDocument();
  });

  it('shows distribution analysis panel', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    const statsTab = screen.getByText('Statistical Measures');
    fireEvent.click(statsTab);

    expect(screen.getByText('Distribution Analysis')).toBeInTheDocument();
    expect(screen.getByText('Skewness: Negative')).toBeInTheDocument();
    expect(screen.getByText('More frequent small gains, occasional large losses')).toBeInTheDocument();
  });

  it('displays relative metrics when available', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    const relativeTab = screen.getByText('Relative Metrics');
    fireEvent.click(relativeTab);

    expect(screen.getByText('Benchmark Relative Metrics')).toBeInTheDocument();
    expect(screen.getByText('Information Ratio')).toBeInTheDocument();
    expect(screen.getByText('Beta')).toBeInTheDocument();
    expect(screen.getByText('Alpha')).toBeInTheDocument();
    expect(screen.getByText('Correlation')).toBeInTheDocument();
    expect(screen.getByText('R-Squared')).toBeInTheDocument();
  });

  it('shows positive alpha in success color', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    const relativeTab = screen.getByText('Relative Metrics');
    fireEvent.click(relativeTab);

    const alphaValue = screen.getByText('2.00%');
    expect(alphaValue).toHaveClass('MuiTypography-colorSuccess');
  });

  it('does not show relative metrics tab when not available', () => {
    const metricsWithoutRelative = {
      ...mockRiskMetricsData,
      relative_metrics: undefined,
    };

    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: metricsWithoutRelative,
          loading: false,
          error: null,
        },
      },
    });

    expect(screen.queryByText('Relative Metrics')).not.toBeInTheDocument();
  });

  it('shows tooltips for complex metrics', () => {
    renderWithProviders(<RiskAnalysis />, {
      initialState: {
        riskMetrics: {
          data: mockRiskMetricsData,
          loading: false,
          error: null,
        },
      },
    });

    // Check for info icons that indicate tooltips
    const infoIcons = screen.getAllByTestId('InfoIcon');
    expect(infoIcons.length).toBeGreaterThan(0);
  });
});