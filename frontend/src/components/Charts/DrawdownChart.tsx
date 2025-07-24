import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Box, Typography, useTheme, Chip, IconButton, Tooltip as MuiTooltip } from '@mui/material';
import { Download as DownloadIcon, Image as ImageIcon } from '@mui/icons-material';
import { format } from 'date-fns';
import { exportChartToPNG, exportDataToCSV } from '../../utils/chartExport';

interface DrawdownChartProps {
  data: Array<{
    date: string;
    drawdown: number; // Negative percentage values
    duration?: number; // Days in drawdown
  }>;
  title?: string;
  height?: number;
  maxDrawdown?: number;
  maxDrawdownDuration?: number;
  id?: string;
}

const DrawdownChart: React.FC<DrawdownChartProps> = ({
  data,
  title = 'Drawdown Analysis',
  height = 300,
  maxDrawdown,
  maxDrawdownDuration,
  id = 'drawdown-chart',
}) => {
  const theme = useTheme();
  
  const handleExportPNG = async () => {
    try {
      await exportChartToPNG(id, `drawdown-${format(new Date(), 'yyyy-MM-dd')}.png`);
    } catch (error) {
      console.error('Failed to export chart as PNG:', error);
    }
  };

  const handleExportCSV = () => {
    try {
      const exportData = data.map(point => ({
        Date: format(new Date(point.date), 'yyyy-MM-dd'),
        'Drawdown (%)': point.drawdown.toFixed(2),
        ...(point.duration ? { 'Duration (days)': point.duration } : {}),
      }));
      exportDataToCSV(exportData, `drawdown-data-${format(new Date(), 'yyyy-MM-dd')}.csv`);
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

  const formatPercent = (value: number) => {
    return `${value.toFixed(2)}%`;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const drawdown = payload[0].value;
      const duration = payload[0].payload.duration;

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
          <Typography
            variant="body2"
            sx={{
              color: drawdown < -5 ? theme.palette.error.main : theme.palette.warning.main,
              fontWeight: 'bold',
              mt: 0.5,
            }}
          >
            Drawdown: {formatPercent(drawdown)}
          </Typography>
          {duration && (
            <Typography variant="caption" color="textSecondary">
              Duration: {duration} days
            </Typography>
          )}
        </Box>
      );
    }
    return null;
  };

  const gradientOffset = () => {
    const dataMax = Math.max(...data.map((d) => d.drawdown));
    const dataMin = Math.min(...data.map((d) => d.drawdown));

    if (dataMax <= 0) {
      return 0;
    } else if (dataMin >= 0) {
      return 1;
    } else {
      return dataMax / (dataMax - dataMin);
    }
  };

  const off = gradientOffset();

  return (
    <Box id={id}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
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
        <Box sx={{ display: 'flex', gap: 1 }}>
          {maxDrawdown !== undefined && (
            <Chip
              label={`Max: ${formatPercent(maxDrawdown)}`}
              size="small"
              color={maxDrawdown < -20 ? 'error' : 'warning'}
              variant="outlined"
            />
          )}
          {maxDrawdownDuration !== undefined && (
            <Chip
              label={`Max Duration: ${maxDrawdownDuration}d`}
              size="small"
              variant="outlined"
            />
          )}
        </Box>
      </Box>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart
          data={data}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <defs>
            <linearGradient id="splitColor" x1="0" y1="0" x2="0" y2="1">
              <stop offset={off} stopColor={theme.palette.success.main} stopOpacity={0.3} />
              <stop offset={off} stopColor={theme.palette.error.main} stopOpacity={0.3} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
          <XAxis
            dataKey="date"
            tickFormatter={formatDate}
            stroke={theme.palette.text.secondary}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            tickFormatter={formatPercent}
            stroke={theme.palette.text.secondary}
            tick={{ fontSize: 12 }}
            domain={['dataMin', 0]}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0} stroke={theme.palette.divider} />
          <ReferenceLine
            y={-5}
            stroke={theme.palette.warning.main}
            strokeDasharray="3 3"
            opacity={0.5}
          />
          <ReferenceLine
            y={-10}
            stroke={theme.palette.error.main}
            strokeDasharray="3 3"
            opacity={0.5}
          />
          <Area
            type="monotone"
            dataKey="drawdown"
            stroke={theme.palette.error.main}
            strokeWidth={2}
            fill="url(#splitColor)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </Box>
  );
};

export default DrawdownChart;