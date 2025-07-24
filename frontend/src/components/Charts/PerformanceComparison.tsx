import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { Box, Typography, useTheme, Paper, Grid } from '@mui/material';

interface Strategy {
  name: string;
  totalReturn: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
}

interface PerformanceComparisonProps {
  strategies: Strategy[];
  title?: string;
  height?: number;
}

const PerformanceComparison: React.FC<PerformanceComparisonProps> = ({
  strategies,
  title = 'Strategy Performance Comparison',
  height = 300,
}) => {
  const theme = useTheme();

  // Prepare data for bar chart
  const barChartData = strategies.map((strategy) => ({
    name: strategy.name,
    'Total Return (%)': strategy.totalReturn,
    'Sharpe Ratio': strategy.sharpeRatio,
    'Win Rate (%)': strategy.winRate,
  }));

  // Prepare data for radar chart
  const radarChartData = [
    {
      metric: 'Return',
      ...strategies.reduce((acc, strategy) => ({
        ...acc,
        [strategy.name]: Math.min(100, Math.max(0, (strategy.totalReturn + 50) * 2)), // Normalize to 0-100
      }), {}),
    },
    {
      metric: 'Sharpe',
      ...strategies.reduce((acc, strategy) => ({
        ...acc,
        [strategy.name]: Math.min(100, Math.max(0, strategy.sharpeRatio * 33.33)), // Normalize to 0-100
      }), {}),
    },
    {
      metric: 'Risk',
      ...strategies.reduce((acc, strategy) => ({
        ...acc,
        [strategy.name]: Math.min(100, Math.max(0, 100 + strategy.maxDrawdown * 2)), // Normalize to 0-100
      }), {}),
    },
    {
      metric: 'Win Rate',
      ...strategies.reduce((acc, strategy) => ({
        ...acc,
        [strategy.name]: strategy.winRate,
      }), {}),
    },
    {
      metric: 'Profit Factor',
      ...strategies.reduce((acc, strategy) => ({
        ...acc,
        [strategy.name]: Math.min(100, Math.max(0, strategy.profitFactor * 25)), // Normalize to 0-100
      }), {}),
    },
  ];

  const colors = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.error.main,
    theme.palette.warning.main,
    theme.palette.success.main,
  ];

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
          <Typography variant="body2" fontWeight="bold">
            {label}
          </Typography>
          {payload.map((entry: any, index: number) => (
            <Typography
              key={index}
              variant="body2"
              sx={{ color: entry.color, mt: 0.5 }}
            >
              {entry.name}: {entry.value.toFixed(2)}
            </Typography>
          ))}
        </Box>
      );
    }
    return null;
  };

  return (
    <Box>
      {title && (
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
      )}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Key Metrics Comparison
            </Typography>
            <ResponsiveContainer width="100%" height={height}>
              <BarChart
                data={barChartData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                <XAxis
                  dataKey="name"
                  stroke={theme.palette.text.secondary}
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  stroke={theme.palette.text.secondary}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Bar dataKey="Total Return (%)" fill={colors[0]} />
                <Bar dataKey="Sharpe Ratio" fill={colors[1]} />
                <Bar dataKey="Win Rate (%)" fill={colors[2]} />
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle1" gutterBottom>
              Strategy Profile Comparison
            </Typography>
            <ResponsiveContainer width="100%" height={height}>
              <RadarChart data={radarChartData}>
                <PolarGrid stroke={theme.palette.divider} />
                <PolarAngleAxis
                  dataKey="metric"
                  stroke={theme.palette.text.secondary}
                  tick={{ fontSize: 12 }}
                />
                <PolarRadiusAxis
                  angle={90}
                  domain={[0, 100]}
                  stroke={theme.palette.text.secondary}
                  tick={{ fontSize: 10 }}
                />
                {strategies.map((strategy, index) => (
                  <Radar
                    key={strategy.name}
                    name={strategy.name}
                    dataKey={strategy.name}
                    stroke={colors[index % colors.length]}
                    fill={colors[index % colors.length]}
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                ))}
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PerformanceComparison;