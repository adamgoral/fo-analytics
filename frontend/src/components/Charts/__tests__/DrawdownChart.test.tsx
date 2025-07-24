import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import DrawdownChart from '../DrawdownChart';
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
  { date: '2024-01-01', drawdown: 0, duration: 0 },
  { date: '2024-01-02', drawdown: -2.5, duration: 1 },
  { date: '2024-01-03', drawdown: -5.0, duration: 2 },
];

describe('DrawdownChart', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with default props', () => {
    render(
      <ThemeProvider theme={theme}>
        <DrawdownChart data={mockData} />
      </ThemeProvider>
    );

    expect(screen.getByText('Drawdown Analysis')).toBeInTheDocument();
  });

  it('renders with custom title', () => {
    render(
      <ThemeProvider theme={theme}>
        <DrawdownChart data={mockData} title="Risk Analysis" />
      </ThemeProvider>
    );

    expect(screen.getByText('Risk Analysis')).toBeInTheDocument();
  });

  it('displays max drawdown chip when provided', () => {
    render(
      <ThemeProvider theme={theme}>
        <DrawdownChart data={mockData} maxDrawdown={-15.5} />
      </ThemeProvider>
    );

    expect(screen.getByText('Max: -15.50%')).toBeInTheDocument();
  });

  it('displays max duration chip when provided', () => {
    render(
      <ThemeProvider theme={theme}>
        <DrawdownChart data={mockData} maxDrawdownDuration={30} />
      </ThemeProvider>
    );

    expect(screen.getByText('Max Duration: 30d')).toBeInTheDocument();
  });

  it('shows export buttons', () => {
    render(
      <ThemeProvider theme={theme}>
        <DrawdownChart data={mockData} />
      </ThemeProvider>
    );

    expect(screen.getByLabelText('Export as PNG')).toBeInTheDocument();
    expect(screen.getByLabelText('Export as CSV')).toBeInTheDocument();
  });

  it('exports chart as PNG when button clicked', async () => {
    render(
      <ThemeProvider theme={theme}>
        <DrawdownChart data={mockData} id="test-drawdown" />
      </ThemeProvider>
    );

    const exportPngButton = screen.getByLabelText('Export as PNG');
    fireEvent.click(exportPngButton);

    expect(chartExport.exportChartToPNG).toHaveBeenCalledWith(
      'test-drawdown',
      expect.stringContaining('drawdown-')
    );
  });

  it('exports data as CSV when button clicked', () => {
    render(
      <ThemeProvider theme={theme}>
        <DrawdownChart data={mockData} />
      </ThemeProvider>
    );

    const exportCsvButton = screen.getByLabelText('Export as CSV');
    fireEvent.click(exportCsvButton);

    expect(chartExport.exportDataToCSV).toHaveBeenCalled();
    const callArgs = (chartExport.exportDataToCSV as any).mock.calls[0];
    expect(callArgs[0]).toHaveLength(3);
    // First item has duration 0, which is falsy, so it shouldn't have 'Duration (days)' property
    expect(callArgs[0][0]).toEqual({
      Date: '2024-01-01',
      'Drawdown (%)': '0.00',
    });
    expect(callArgs[0][0]).not.toHaveProperty('Duration (days)');
    // Second item should have duration
    expect(callArgs[0][1]).toMatchObject({
      Date: '2024-01-02',
      'Drawdown (%)': '-2.50',
      'Duration (days)': 1,
    });
    expect(callArgs[1]).toMatch(/^drawdown-data-\d{4}-\d{2}-\d{2}\.csv$/);
  });

  it('handles data without duration gracefully', () => {
    const dataWithoutDuration = [
      { date: '2024-01-01', drawdown: 0 },
      { date: '2024-01-02', drawdown: -2.5 },
    ];

    render(
      <ThemeProvider theme={theme}>
        <DrawdownChart data={dataWithoutDuration} />
      </ThemeProvider>
    );

    const exportCsvButton = screen.getByLabelText('Export as CSV');
    fireEvent.click(exportCsvButton);

    const exportedData = (chartExport.exportDataToCSV as any).mock.calls[0][0];
    expect(exportedData[0]).not.toHaveProperty('Duration (days)');
  });

  it('applies correct color to max drawdown chip based on severity', () => {
    const { rerender } = render(
      <ThemeProvider theme={theme}>
        <DrawdownChart data={mockData} maxDrawdown={-5} />
      </ThemeProvider>
    );

    // Warning color for moderate drawdown
    expect(screen.getByText('Max: -5.00%').parentElement).toHaveClass('MuiChip-outlinedWarning');

    // Error color for severe drawdown
    rerender(
      <ThemeProvider theme={theme}>
        <DrawdownChart data={mockData} maxDrawdown={-25} />
      </ThemeProvider>
    );

    expect(screen.getByText('Max: -25.00%').parentElement).toHaveClass('MuiChip-outlinedError');
  });
});