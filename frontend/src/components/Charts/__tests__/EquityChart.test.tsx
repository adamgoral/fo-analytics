import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import EquityChart from '../EquityChart';
import * as chartExport from '../../../utils/chartExport';

// Mock the export utilities
vi.mock('../../../utils/chartExport', () => ({
  exportChartToPNG: vi.fn(),
  exportDataToCSV: vi.fn(),
}));

// Mock recharts to avoid rendering issues in tests
vi.mock('recharts', () => import('../../../test/mocks/recharts'));

const theme = createTheme();

const mockData = [
  { date: '2024-01-01', equity: 100000, benchmark: 100000 },
  { date: '2024-01-02', equity: 101000, benchmark: 100500 },
  { date: '2024-01-03', equity: 102500, benchmark: 101200 },
];

describe('EquityChart', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with default props', () => {
    render(
      <ThemeProvider theme={theme}>
        <EquityChart data={mockData} />
      </ThemeProvider>
    );

    expect(screen.getByText('Equity Curve')).toBeInTheDocument();
  });

  it('renders with custom title', () => {
    render(
      <ThemeProvider theme={theme}>
        <EquityChart data={mockData} title="Custom Title" />
      </ThemeProvider>
    );

    expect(screen.getByText('Custom Title')).toBeInTheDocument();
  });

  it('shows export buttons', () => {
    render(
      <ThemeProvider theme={theme}>
        <EquityChart data={mockData} />
      </ThemeProvider>
    );

    expect(screen.getByLabelText('Export as PNG')).toBeInTheDocument();
    expect(screen.getByLabelText('Export as CSV')).toBeInTheDocument();
  });

  it('exports chart as PNG when button clicked', async () => {
    render(
      <ThemeProvider theme={theme}>
        <EquityChart data={mockData} id="test-chart" />
      </ThemeProvider>
    );

    const exportPngButton = screen.getByLabelText('Export as PNG');
    fireEvent.click(exportPngButton);

    expect(chartExport.exportChartToPNG).toHaveBeenCalledWith(
      'test-chart',
      expect.stringContaining('equity-curve-')
    );
  });

  it('exports data as CSV when button clicked', () => {
    render(
      <ThemeProvider theme={theme}>
        <EquityChart data={mockData} showBenchmark={true} />
      </ThemeProvider>
    );

    const exportCsvButton = screen.getByLabelText('Export as CSV');
    fireEvent.click(exportCsvButton);

    expect(chartExport.exportDataToCSV).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({
          Date: '2024-01-01',
          Equity: '100000.00',
          Benchmark: '100000.00',
        }),
      ]),
      expect.stringContaining('equity-data-')
    );
  });

  it('handles empty data gracefully', () => {
    render(
      <ThemeProvider theme={theme}>
        <EquityChart data={[]} />
      </ThemeProvider>
    );

    expect(screen.getByText('Equity Curve')).toBeInTheDocument();
  });

  it('does not include benchmark in CSV when showBenchmark is false', () => {
    render(
      <ThemeProvider theme={theme}>
        <EquityChart data={mockData} showBenchmark={false} />
      </ThemeProvider>
    );

    const exportCsvButton = screen.getByLabelText('Export as CSV');
    fireEvent.click(exportCsvButton);

    const exportedData = (chartExport.exportDataToCSV as any).mock.calls[0][0];
    expect(exportedData[0]).not.toHaveProperty('Benchmark');
  });
});