import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  ListItemSecondaryAction,
  Tabs,
  Tab,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  type SelectChangeEvent,
  Grid,
} from '@mui/material';
import {
  TrendingUp as StrategyIcon,
  MoreVert as MoreIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  Code as CodeIcon,
  Assessment as BacktestIcon,
} from '@mui/icons-material';

interface Strategy {
  id: string;
  name: string;
  description: string;
  framework: 'backtrader' | 'zipline' | 'quantlib';
  status: 'draft' | 'ready' | 'validated';
  performance: {
    sharpeRatio: number;
    maxDrawdown: number;
    totalReturn: number;
  } | null;
  documentSource: string;
  createdAt: string;
  lastBacktest: string | null;
}

const StrategiesPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(null);
  const [backtestDialogOpen, setBacktestDialogOpen] = useState(false);
  const [backtestParams, setBacktestParams] = useState({
    startDate: '2023-01-01',
    endDate: '2024-01-01',
    initialCapital: '100000',
    framework: 'backtrader',
  });

  // Mock data - in real app this would come from API
  const [strategies] = useState<Strategy[]>([
    {
      id: '1',
      name: 'Momentum Alpha Strategy',
      description: 'Long momentum positions in trending stocks with risk management overlay',
      framework: 'backtrader',
      status: 'validated',
      performance: {
        sharpeRatio: 1.45,
        maxDrawdown: -12.3,
        totalReturn: 23.7,
      },
      documentSource: 'Q4 Trading Strategy.pdf',
      createdAt: '2024-01-15T10:30:00Z',
      lastBacktest: '2024-01-20T14:20:00Z',
    },
    {
      id: '2',
      name: 'Mean Reversion Strategy',
      description: 'Contrarian approach targeting oversold conditions in large-cap stocks',
      framework: 'zipline',
      status: 'ready',
      performance: {
        sharpeRatio: 0.89,
        maxDrawdown: -8.7,
        totalReturn: 15.2,
      },
      documentSource: 'Market Analysis Q3.pdf',
      createdAt: '2024-01-14T14:20:00Z',
      lastBacktest: '2024-01-18T09:15:00Z',
    },
    {
      id: '3',
      name: 'Risk Parity Portfolio',
      description: 'Equal risk contribution across asset classes with dynamic rebalancing',
      framework: 'quantlib',
      status: 'draft',
      performance: null,
      documentSource: 'Risk Management Framework.pdf',
      createdAt: '2024-01-13T09:15:00Z',
      lastBacktest: null,
    },
  ]);

  const filteredStrategies = strategies.filter(strategy => {
    switch (activeTab) {
      case 0:
        return true; // All strategies
      case 1:
        return strategy.status === 'validated';
      case 2:
        return strategy.status === 'ready';
      case 3:
        return strategy.status === 'draft';
      default:
        return true;
    }
  });

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getStatusColor = (status: Strategy['status']) => {
    switch (status) {
      case 'validated':
        return 'success';
      case 'ready':
        return 'primary';
      case 'draft':
        return 'default';
      default:
        return 'default';
    }
  };

  const getFrameworkColor = (framework: Strategy['framework']) => {
    switch (framework) {
      case 'backtrader':
        return 'primary';
      case 'zipline':
        return 'secondary';
      case 'quantlib':
        return 'info';
      default:
        return 'default';
    }
  };

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, strategyId: string) => {
    setMenuAnchor(event.currentTarget);
    setSelectedStrategyId(strategyId);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedStrategyId(null);
  };

  const handleAction = (action: string) => {
    console.log(`${action} strategy:`, selectedStrategyId);
    if (action === 'backtest') {
      setBacktestDialogOpen(true);
    }
    handleMenuClose();
  };

  const handleBacktestParamChange = (field: string) => (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | SelectChangeEvent<string>
  ) => {
    setBacktestParams({
      ...backtestParams,
      [field]: event.target.value,
    });
  };

  const handleRunBacktest = () => {
    console.log('Running backtest with params:', backtestParams);
    setBacktestDialogOpen(false);
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 1, fontWeight: 600 }}>
          Trading Strategies
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage and analyze your extracted trading strategies
        </Typography>
      </Box>

      {/* Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
                {strategies.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Strategies
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
                {strategies.filter(s => s.status === 'validated').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Validated
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" sx={{ fontWeight: 600, mb: 1, color: 'success.main' }}>
                {strategies
                  .filter(s => s.performance)
                  .reduce((avg, s) => avg + s.performance!.sharpeRatio, 0) /
                  strategies.filter(s => s.performance).length || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg. Sharpe Ratio
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" sx={{ fontWeight: 600, mb: 1, color: 'primary.main' }}>
                {strategies
                  .filter(s => s.performance)
                  .reduce((avg, s) => avg + s.performance!.totalReturn, 0) /
                  strategies.filter(s => s.performance).length || 0}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg. Return
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs and Strategy List */}
      <Card>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange}>
            <Tab label={`All (${strategies.length})`} />
            <Tab label={`Validated (${strategies.filter(s => s.status === 'validated').length})`} />
            <Tab label={`Ready (${strategies.filter(s => s.status === 'ready').length})`} />
            <Tab label={`Draft (${strategies.filter(s => s.status === 'draft').length})`} />
          </Tabs>
        </Box>

        <CardContent>
          {filteredStrategies.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <StrategyIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                No strategies found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Upload documents to extract trading strategies
              </Typography>
            </Box>
          ) : (
            <List>
              {filteredStrategies.map((strategy, index) => (
                <ListItem
                  key={strategy.id}
                  divider={index < filteredStrategies.length - 1}
                  sx={{ px: 0, py: 2 }}
                >
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: 'success.main' }}>
                      <StrategyIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                          {strategy.name}
                        </Typography>
                        <Chip
                          label={strategy.status}
                          size="small"
                          color={getStatusColor(strategy.status)}
                          variant="outlined"
                        />
                        <Chip
                          label={strategy.framework}
                          size="small"
                          color={getFrameworkColor(strategy.framework)}
                          variant="filled"
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          {strategy.description}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Source: {strategy.documentSource} • Created {formatDate(strategy.createdAt)}
                        </Typography>
                        {strategy.performance && (
                          <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                            <Typography variant="body2" color="success.main">
                              Sharpe: {strategy.performance.sharpeRatio.toFixed(2)}
                            </Typography>
                            <Typography variant="body2" color="primary.main">
                              Return: {strategy.performance.totalReturn.toFixed(1)}%
                            </Typography>
                            <Typography variant="body2" color="error.main">
                              Max DD: {strategy.performance.maxDrawdown.toFixed(1)}%
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={(e) => handleMenuOpen(e, strategy.id)}
                    >
                      <MoreIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Action Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleAction('view')}>
          <ViewIcon sx={{ mr: 2 }} />
          View Details
        </MenuItem>
        <MenuItem onClick={() => handleAction('backtest')}>
          <BacktestIcon sx={{ mr: 2 }} />
          Run Backtest
        </MenuItem>
        <MenuItem onClick={() => handleAction('code')}>
          <CodeIcon sx={{ mr: 2 }} />
          View Code
        </MenuItem>
        <MenuItem onClick={() => handleAction('edit')}>
          <EditIcon sx={{ mr: 2 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={() => handleAction('delete')} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 2 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Backtest Dialog */}
      <Dialog
        open={backtestDialogOpen}
        onClose={() => setBacktestDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Run Backtest</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Start Date"
                  type="date"
                  value={backtestParams.startDate}
                  onChange={handleBacktestParamChange('startDate')}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="End Date"
                  type="date"
                  value={backtestParams.endDate}
                  onChange={handleBacktestParamChange('endDate')}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Initial Capital"
                  type="number"
                  value={backtestParams.initialCapital}
                  onChange={handleBacktestParamChange('initialCapital')}
                />
              </Grid>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Framework</InputLabel>
                  <Select
                    value={backtestParams.framework}
                    label="Framework"
                    onChange={handleBacktestParamChange('framework')}
                  >
                    <MenuItem value="backtrader">Backtrader</MenuItem>
                    <MenuItem value="zipline">Zipline</MenuItem>
                    <MenuItem value="quantlib">QuantLib</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBacktestDialogOpen(false)}>
            Cancel
          </Button>
          <Button onClick={handleRunBacktest} variant="contained">
            Run Backtest
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StrategiesPage;