import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Box, Typography, useTheme, IconButton, Tooltip as MuiTooltip } from '@mui/material';
import { Download as DownloadIcon, Image as ImageIcon } from '@mui/icons-material';
import { format } from 'date-fns';
import { exportChartToPNG, exportDataToCSV } from '../../utils/chartExport';

interface EquityChartProps {
  data: Array<{
    date: string;
    equity: number;
    benchmark?: number;
  }>;
  title?: string;
  height?: number;
  showBenchmark?: boolean;
  id?: string;
}

const EquityChart: React.FC<EquityChartProps> = ({
  data,
  title = 'Equity Curve',
  height = 400,
  showBenchmark = false,
  id = 'equity-chart',
}) => {
  const theme = useTheme();
  
  const handleExportPNG = async () => {
    try {
      await exportChartToPNG(id, `equity-curve-${format(new Date(), 'yyyy-MM-dd')}.png`);
    } catch (error) {
      console.error('Failed to export chart as PNG:', error);
    }
  };

  const handleExportCSV = () => {
    try {
      const exportData = data.map(point => ({
        Date: format(new Date(point.date), 'yyyy-MM-dd'),
        Equity: point.equity.toFixed(2),
        ...(showBenchmark && point.benchmark ? { Benchmark: point.benchmark.toFixed(2) } : {}),
      }));
      exportDataToCSV(exportData, `equity-data-${format(new Date(), 'yyyy-MM-dd')}.csv`);
    } catch (error) {
      console.error('Failed to export data as CSV:', error);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return format(new Date(dateStr), 'MMM dd, yyyy');
    } catch {
      return dateStr;
    }
  };

  const formatValue = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    const baseValue = data[0]?.equity || 100000;
    const percentChange = ((value - baseValue) / baseValue) * 100;
    return `${percentChange >= 0 ? '+' : ''}${percentChange.toFixed(2)}%`;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Box
          sx={{
            backgroundColor: theme.palette.background.paper,
            border: 1,
            borderColor: theme.palette.divider,
            p: 1.5,
            borderRadius: 1,
          }}
        >
          <Typography variant="body2" color="textSecondary">
            {formatDate(label)}
          </Typography>
          {payload.map((entry: any, index: number) => (
            <Box key={index} sx={{ mt: 0.5 }}>
              <Typography
                variant="body2"
                sx={{ color: entry.color, fontWeight: 'bold' }}
              >
                {entry.name}: {formatValue(entry.value)}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {formatPercent(entry.value)}
              </Typography>
            </Box>
          ))}
        </Box>
      );
    }
    return null;
  };

  const initialEquity = data[0]?.equity || 100000;

  return (
    <Box id={id}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        {title && (
          <Typography variant="h6">
            {title}
          </Typography>
        )}
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <MuiTooltip title="Export as PNG">
            <IconButton size="small" onClick={handleExportPNG}>
              <ImageIcon fontSize="small" />
            </IconButton>
          </MuiTooltip>
          <MuiTooltip title="Export as CSV">
            <IconButton size="small" onClick={handleExportCSV}>
              <DownloadIcon fontSize="small" />
            </IconButton>
          </MuiTooltip>
        </Box>
      </Box>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            stroke={theme.palette.text.secondary}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            tickFormatter={formatValue}
            stroke={theme.palette.text.secondary}
            tick={{ fontSize: 12 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <ReferenceLine
            y={initialEquity}
            stroke={theme.palette.text.secondary}
            strokeDasharray="5 5"
            label={{
              value: 'Initial',
              position: 'left',
              fill: theme.palette.text.secondary,
            }}
          />
          <Line
            type="monotone"
            dataKey="equity"
            name="Strategy"
            stroke={theme.palette.primary.main}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
          {showBenchmark && (
            <Line
              type="monotone"
              dataKey="benchmark"
              name="Benchmark"
              stroke={theme.palette.secondary.main}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default EquityChart;