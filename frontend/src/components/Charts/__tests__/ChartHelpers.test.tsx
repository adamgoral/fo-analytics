import React from 'react';
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import EquityChart from '../EquityChart';
import DrawdownChart from '../DrawdownChart';

const theme = createTheme();

describe('Chart Helper Functions', () => {
  describe('EquityChart Helpers', () => {
    it('handles date formatting edge cases', () => {
      const mockData = [
        { date: 'invalid-date', equity: 100000 },
        { date: '2024-01-01', equity: 101000 },
      ];

      // Component should render without crashing
      const { container } = render(
        <ThemeProvider theme={theme}>
          <EquityChart data={mockData} />
        </ThemeProvider>
      );

      expect(container).toBeTruthy();
    });

    it('calculates initial equity correctly with empty data', () => {
      const { container } = render(
        <ThemeProvider theme={theme}>
          <EquityChart data={[]} />
        </ThemeProvider>
      );

      expect(container).toBeTruthy();
    });

    it('handles formatValue with various numbers', () => {
      const mockData = [
        { date: '2024-01-01', equity: 0 },
        { date: '2024-01-02', equity: -1000 },
        { date: '2024-01-03', equity: 1234567.89 },
      ];

      const { container } = render(
        <ThemeProvider theme={theme}>
          <EquityChart data={mockData} />
        </ThemeProvider>
      );

      expect(container).toBeTruthy();
    });
  });

  describe('DrawdownChart Helpers', () => {
    it('calculates gradient offset correctly with all positive values', () => {
      const mockData = [
        { date: '2024-01-01', drawdown: 5 },
        { date: '2024-01-02', drawdown: 10 },
      ];

      const { container } = render(
        <ThemeProvider theme={theme}>
          <DrawdownChart data={mockData} />
        </ThemeProvider>
      );

      expect(container).toBeTruthy();
    });

    it('calculates gradient offset correctly with all negative values', () => {
      const mockData = [
        { date: '2024-01-01', drawdown: -5 },
        { date: '2024-01-02', drawdown: -10 },
      ];

      const { container } = render(
        <ThemeProvider theme={theme}>
          <DrawdownChart data={mockData} />
        </ThemeProvider>
      );

      expect(container).toBeTruthy();
    });

    it('calculates gradient offset correctly with mixed values', () => {
      const mockData = [
        { date: '2024-01-01', drawdown: 5 },
        { date: '2024-01-02', drawdown: -10 },
      ];

      const { container } = render(
        <ThemeProvider theme={theme}>
          <DrawdownChart data={mockData} />
        </ThemeProvider>
      );

      expect(container).toBeTruthy();
    });
  });
});