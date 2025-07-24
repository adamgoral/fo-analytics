import React from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
} from '@mui/material';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts';
import { useAppSelector } from '../../../store';

const COLORS = [
  '#0088FE', '#00C49F', '#FFBB28', '#FF8042',
  '#8884D8', '#82CA9D', '#FFC658', '#FF6B6B',
  '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'
];

const AllocationChart: React.FC = () => {
  const { currentPortfolio } = useAppSelector((state) => state.portfolio);

  if (!currentPortfolio || !currentPortfolio.allocation_by_asset_class) {
    return (
      <Paper sx={{ p: 3, textAlign: 'center', height: '100%' }}>
        <Typography variant="h6" color="textSecondary">
          No allocation data available
        </Typography>
      </Paper>
    );
  }

  // Prepare data for pie chart
  const chartData = Object.entries(currentPortfolio.allocation_by_asset_class).map(
    ([assetClass, allocation]) => ({
      name: assetClass,
      value: allocation * 100, // Convert to percentage
    })
  );

  // Prepare data for position breakdown by symbol
  const positionData = currentPortfolio.positions
    ?.sort((a, b) => b.weight - a.weight)
    .slice(0, 10) // Top 10 positions
    .map(position => ({
      symbol: position.symbol,
      weight: position.weight * 100,
      assetClass: position.asset_class,
    }));

  const formatTooltipValue = (value: number) => `${value.toFixed(2)}%`;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <Paper sx={{ p: 1 }}>
          <Typography variant="body2">{label}</Typography>
          <Typography variant="body2" color="primary">
            {formatTooltipValue(payload[0].value)}
          </Typography>
        </Paper>
      );
    }
    return null;
  };

  return (
    <Box sx={{ height: '100%' }}>
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Asset Allocation
        </Typography>
        
        <Box sx={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value.toFixed(1)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </Box>

        <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
          {chartData.map((entry, index) => (
            <Box key={entry.name} sx={{ display: 'flex', alignItems: 'center' }}>
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  backgroundColor: COLORS[index % COLORS.length],
                  borderRadius: '50%',
                  mr: 0.5,
                }}
              />
              <Typography variant="caption">
                {entry.name}: {entry.value.toFixed(1)}%
              </Typography>
            </Box>
          ))}
        </Box>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Top Holdings
        </Typography>
        
        <List dense>
          {positionData?.map((position, index) => (
            <ListItem
              key={position.symbol}
              sx={{
                py: 1,
                borderBottom: index < positionData.length - 1 ? 1 : 0,
                borderColor: 'divider',
              }}
            >
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Typography variant="subtitle2">{position.symbol}</Typography>
                    <Typography variant="body2" color="primary">
                      {position.weight.toFixed(2)}%
                    </Typography>
                  </Box>
                }
                secondary={
                  <Chip
                    label={position.assetClass}
                    size="small"
                    variant="outlined"
                    sx={{ mt: 0.5 }}
                  />
                }
              />
            </ListItem>
          ))}
        </List>
        
        {currentPortfolio.positions && currentPortfolio.positions.length > 10 && (
          <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
            Showing top 10 of {currentPortfolio.positions.length} holdings
          </Typography>
        )}
      </Paper>
    </Box>
  );
};

export default AllocationChart;