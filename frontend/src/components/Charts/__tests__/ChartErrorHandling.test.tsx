import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import EquityChart from '../EquityChart';
import DrawdownChart from '../DrawdownChart';
import * as chartExport from '../../../utils/chartExport';

// Mock the export utilities
vi.mock('../../../utils/chartExport', () => ({
  exportChartToPNG: vi.fn(),
  exportDataToCSV: vi.fn(),
}));

// Mock recharts
vi.mock('recharts', () => import('../../../test/mocks/recharts'));

const theme = createTheme();

describe('Chart Error Handling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset console mocks
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('EquityChart Error Handling', () => {
    const mockData = [
      { date: '2024-01-01', equity: 100000 },
      { date: 'invalid-date', equity: 101000 },
    ];

    it('handles date formatting errors gracefully', () => {
      render(
        <ThemeProvider theme={theme}>
          <EquityChart data={mockData} />
        </ThemeProvider>
      );

      // Component should still render
      expect(screen.getByText('Equity Curve')).toBeInTheDocument();
    });

    it('handles PNG export errors', async () => {
      (chartExport.exportChartToPNG as any).mockRejectedValue(new Error('Export failed'));

      render(
        <ThemeProvider theme={theme}>
          <EquityChart data={mockData} />
        </ThemeProvider>
      );

      const exportButton = screen.getByLabelText('Export as PNG');
      fireEvent.click(exportButton);

      await vi.waitFor(() => {
        expect(console.error).toHaveBeenCalledWith(
          'Failed to export chart as PNG:',
          expect.any(Error)
        );
      });
    });

    it('handles CSV export errors', () => {
      (chartExport.exportDataToCSV as any).mockImplementation(() => {
        throw new Error('CSV export failed');
      });

      render(
        <ThemeProvider theme={theme}>
          <EquityChart data={mockData} />
        </ThemeProvider>
      );

      const exportButton = screen.getByLabelText('Export as CSV');
      fireEvent.click(exportButton);

      expect(console.error).toHaveBeenCalledWith(
        'Failed to export data as CSV:',
        expect.any(Error)
      );
    });

    it('handles missing benchmark data gracefully', () => {
      const dataWithoutBenchmark = [
        { date: '2024-01-01', equity: 100000 },
        { date: '2024-01-02', equity: 101000 },
      ];

      render(
        <ThemeProvider theme={theme}>
          <EquityChart data={dataWithoutBenchmark} showBenchmark={true} />
        </ThemeProvider>
      );

      // Should render without crashing
      expect(screen.getByText('Equity Curve')).toBeInTheDocument();
    });
  });

  describe('DrawdownChart Error Handling', () => {
    const mockData = [
      { date: '2024-01-01', drawdown: 0 },
      { date: 'invalid-date', drawdown: -5 },
    ];

    it('handles date formatting errors in DrawdownChart', () => {
      render(
        <ThemeProvider theme={theme}>
          <DrawdownChart data={mockData} />
        </ThemeProvider>
      );

      // Component should still render
      expect(screen.getByText('Drawdown Analysis')).toBeInTheDocument();
    });

    it('handles PNG export errors in DrawdownChart', async () => {
      (chartExport.exportChartToPNG as any).mockRejectedValue(new Error('Export failed'));

      render(
        <ThemeProvider theme={theme}>
          <DrawdownChart data={mockData} />
        </ThemeProvider>
      );

      const exportButton = screen.getByLabelText('Export as PNG');
      fireEvent.click(exportButton);

      await vi.waitFor(() => {
        expect(console.error).toHaveBeenCalledWith(
          'Failed to export chart as PNG:',
          expect.any(Error)
        );
      });
    });

    it('handles CSV export errors in DrawdownChart', () => {
      (chartExport.exportDataToCSV as any).mockImplementation(() => {
        throw new Error('CSV export failed');
      });

      render(
        <ThemeProvider theme={theme}>
          <DrawdownChart data={mockData} />
        </ThemeProvider>
      );

      const exportButton = screen.getByLabelText('Export as CSV');
      fireEvent.click(exportButton);

      expect(console.error).toHaveBeenCalledWith(
        'Failed to export data as CSV:',
        expect.any(Error)
      );
    });
  });
});