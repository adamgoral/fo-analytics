import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Tab,
  Tabs,
  IconButton,
  Divider,
  Alert,
  Chip,
  Tooltip,
  Skeleton,
} from '@mui/material';
import {
  Close as CloseIcon,
  Download as DownloadIcon,
  PlayArrow as RunBacktestIcon,
  Fullscreen as FullscreenIcon,
  FullscreenExit as FullscreenExitIcon,
} from '@mui/icons-material';
import { documentsApi } from '../../services/documents';
import type { DocumentContent, ExtractedStrategy } from '../../services/documents';


interface DocumentViewerProps {
  documentId: string;
  documentName: string;
  onClose: () => void;
  onRunBacktest?: (strategyId: string) => void;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({
  documentId,
  documentName,
  onClose,
  onRunBacktest,
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [content, setContent] = useState<DocumentContent | null>(null);
  const [strategies, setStrategies] = useState<ExtractedStrategy[]>([]);
  const [selectedPage, setSelectedPage] = useState<number | null>(null);
  const [fullscreen, setFullscreen] = useState(false);

  useEffect(() => {
    loadDocumentData();
  }, [documentId]);

  const loadDocumentData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load document content and strategies in parallel
      const [contentResponse, strategiesResponse] = await Promise.all([
        documentsApi.getContent(documentId),
        documentsApi.getStrategies(documentId),
      ]);

      setContent(contentResponse);
      setStrategies(strategiesResponse);
    } catch (err: any) {
      setError(err.message || 'Failed to load document data');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      await documentsApi.download(documentId, documentName);
    } catch (err: any) {
      console.error('Download failed:', err);
    }
  };

  const getRiskLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'low':
        return 'success';
      case 'medium':
        return 'warning';
      case 'high':
        return 'error';
      default:
        return 'default';
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'warning';
    return 'error';
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Skeleton variant="text" width="60%" height={40} />
        <Skeleton variant="rectangular" width="100%" height={400} sx={{ mt: 2 }} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button onClick={loadDocumentData}>Retry</Button>
      </Box>
    );
  }

  return (
    <Paper
      sx={{
        height: fullscreen ? '100vh' : 'calc(100vh - 200px)',
        display: 'flex',
        flexDirection: 'column',
        position: fullscreen ? 'fixed' : 'relative',
        top: fullscreen ? 0 : 'auto',
        left: fullscreen ? 0 : 'auto',
        right: fullscreen ? 0 : 'auto',
        bottom: fullscreen ? 0 : 'auto',
        zIndex: fullscreen ? 1300 : 'auto',
      }}
    >
      {/* Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {documentName}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Download">
              <IconButton onClick={handleDownload}>
                <DownloadIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}>
              <IconButton onClick={() => setFullscreen(!fullscreen)}>
                {fullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Close">
              <IconButton onClick={onClose}>
                <CloseIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        {/* Tabs */}
        <Tabs value={activeTab} onChange={(_, value) => setActiveTab(value)} sx={{ mt: 1 }}>
          <Tab label="Document Content" />
          <Tab label={`Extracted Strategies (${strategies.length})`} />
        </Tabs>
      </Box>

      {/* Content */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        {activeTab === 0 && content && (
          <Box sx={{ p: 3 }}>
            {/* Document metadata */}
            <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
              {content.metadata.file_type && (
                <Chip label={`Type: ${content.metadata.file_type.toUpperCase()}`} size="small" />
              )}
              {content.metadata.pages && (
                <Chip label={`Pages: ${content.metadata.pages}`} size="small" />
              )}
              {content.metadata.created_at && (
                <Chip label={`Created: ${new Date(content.metadata.created_at).toLocaleDateString()}`} size="small" />
              )}
            </Box>

            {/* Page selector if multiple pages */}
            {content.page_contents && content.page_contents.length > 1 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ mb: 1 }}>
                  Select Page:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Button
                    size="small"
                    variant={selectedPage === null ? 'contained' : 'outlined'}
                    onClick={() => setSelectedPage(null)}
                  >
                    All Pages
                  </Button>
                  {content.page_contents.map((page) => (
                    <Button
                      key={page.page_number}
                      size="small"
                      variant={selectedPage === page.page_number ? 'contained' : 'outlined'}
                      onClick={() => setSelectedPage(page.page_number)}
                    >
                      Page {page.page_number}
                    </Button>
                  ))}
                </Box>
              </Box>
            )}

            <Divider sx={{ mb: 2 }} />

            {/* Document text */}
            <Box
              sx={{
                whiteSpace: 'pre-wrap',
                fontFamily: 'monospace',
                fontSize: '0.9rem',
                lineHeight: 1.6,
                p: 2,
                bgcolor: 'background.default',
                borderRadius: 1,
                maxHeight: '600px',
                overflow: 'auto',
              }}
            >
              {selectedPage !== null && content.page_contents
                ? content.page_contents.find(p => p.page_number === selectedPage)?.text || ''
                : content.text}
            </Box>
          </Box>
        )}

        {activeTab === 1 && (
          <Box sx={{ p: 3 }}>
            {strategies.length === 0 ? (
              <Alert severity="info">
                No strategies have been extracted from this document yet.
              </Alert>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {strategies.map((strategy) => (
                  <Paper key={strategy.id} variant="outlined" sx={{ p: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {strategy.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                          {strategy.description}
                        </Typography>
                      </Box>
                      {onRunBacktest && (
                        <Button
                          variant="contained"
                          startIcon={<RunBacktestIcon />}
                          onClick={() => onRunBacktest(strategy.id)}
                          size="small"
                        >
                          Run Backtest
                        </Button>
                      )}
                    </Box>

                    {/* Strategy metadata */}
                    <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                      <Chip label={`Asset: ${strategy.asset_class}`} size="small" />
                      <Chip label={`Timeframe: ${strategy.timeframe}`} size="small" />
                      <Chip 
                        label={`Risk: ${strategy.risk_level}`} 
                        size="small"
                        color={getRiskLevelColor(strategy.risk_level)}
                      />
                      <Chip 
                        label={`Confidence: ${(strategy.confidence_score * 100).toFixed(0)}%`} 
                        size="small"
                        color={getConfidenceColor(strategy.confidence_score)}
                      />
                    </Box>

                    <Divider sx={{ my: 2 }} />

                    {/* Entry and Exit conditions */}
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 2 }}>
                      <Box>
                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                          Entry Conditions
                        </Typography>
                        <ul style={{ margin: 0, paddingLeft: 20 }}>
                          {strategy.entry_conditions.map((condition, idx) => (
                            <li key={idx}>
                              <Typography variant="body2">{condition}</Typography>
                            </li>
                          ))}
                        </ul>
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                          Exit Conditions
                        </Typography>
                        <ul style={{ margin: 0, paddingLeft: 20 }}>
                          {strategy.exit_conditions.map((condition, idx) => (
                            <li key={idx}>
                              <Typography variant="body2">{condition}</Typography>
                            </li>
                          ))}
                        </ul>
                      </Box>
                    </Box>

                    {/* Performance metrics if available */}
                    {strategy.performance_metrics && (
                      <>
                        <Divider sx={{ my: 2 }} />
                        <Box>
                          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                            Expected Performance
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 3 }}>
                            {strategy.performance_metrics.expected_return !== undefined && (
                              <Box>
                                <Typography variant="caption" color="text.secondary">
                                  Expected Return
                                </Typography>
                                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                                  {(strategy.performance_metrics.expected_return * 100).toFixed(1)}%
                                </Typography>
                              </Box>
                            )}
                            {strategy.performance_metrics.sharpe_ratio !== undefined && (
                              <Box>
                                <Typography variant="caption" color="text.secondary">
                                  Sharpe Ratio
                                </Typography>
                                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                                  {strategy.performance_metrics.sharpe_ratio.toFixed(2)}
                                </Typography>
                              </Box>
                            )}
                            {strategy.performance_metrics.max_drawdown !== undefined && (
                              <Box>
                                <Typography variant="caption" color="text.secondary">
                                  Max Drawdown
                                </Typography>
                                <Typography variant="body1" sx={{ fontWeight: 600 }}>
                                  {(strategy.performance_metrics.max_drawdown * 100).toFixed(1)}%
                                </Typography>
                              </Box>
                            )}
                          </Box>
                        </Box>
                      </>
                    )}

                    {/* Risk Management */}
                    {Object.keys(strategy.risk_management).length > 0 && (
                      <>
                        <Divider sx={{ my: 2 }} />
                        <Box>
                          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                            Risk Management
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                            {Object.entries(strategy.risk_management).map(([key, value]) => (
                              <Chip
                                key={key}
                                label={`${key.replace(/_/g, ' ')}: ${value}`}
                                size="small"
                                variant="outlined"
                              />
                            ))}
                          </Box>
                        </Box>
                      </>
                    )}

                    <Box sx={{ mt: 2 }}>
                      <Typography variant="caption" color="text.secondary">
                        Extracted on {new Date(strategy.extracted_at).toLocaleString()}
                      </Typography>
                    </Box>
                  </Paper>
                ))}
              </Box>
            )}
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default DocumentViewer;