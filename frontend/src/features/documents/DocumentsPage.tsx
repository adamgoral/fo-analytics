import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  LinearProgress,
  Alert,
  Snackbar,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Description as DocumentIcon,
  MoreVert as MoreIcon,
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Download as DownloadIcon,
  Visibility as ViewIcon,
  TrendingUp as AnalyzeIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useAuth } from '../../hooks';
import { useWebSocket } from '../../hooks/useWebSocket';
import { 
  DocumentProcessingProgressMessage,
  DocumentProcessingCompletedMessage,
  DocumentProcessingFailedMessage,
  StrategyExtractedMessage,
  WebSocketMessage
} from '../../services/websocket';

interface Document {
  id: string;
  name: string;
  size: number;
  uploadedAt: string;
  status: 'processing' | 'completed' | 'failed';
  strategiesCount: number;
  uploadedBy: string;
  processingProgress?: number;
  processingMessage?: string;
}

const DocumentsPage: React.FC = () => {
  const { canUploadDocuments } = useAuth();
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ message: string; severity: 'success' | 'error' | 'info' } | null>(null);

  // Mock data - in real app this would come from API
  const [documents, setDocuments] = useState<Document[]>([
    {
      id: '1',
      name: 'Q4 Trading Strategy.pdf',
      size: 2400000,
      uploadedAt: '2024-01-15T10:30:00Z',
      status: 'completed',
      strategiesCount: 5,
      uploadedBy: 'John Doe',
    },
    {
      id: '2',
      name: 'Market Analysis Q3.pdf',
      size: 1800000,
      uploadedAt: '2024-01-14T14:20:00Z',
      status: 'processing',
      strategiesCount: 0,
      uploadedBy: 'Jane Smith',
    },
    {
      id: '3',
      name: 'Risk Management Framework.pdf',
      size: 3200000,
      uploadedAt: '2024-01-13T09:15:00Z',
      status: 'failed',
      strategiesCount: 0,
      uploadedBy: 'Mike Johnson',
    },
  ]);

  // WebSocket handlers
  const handleProcessingProgress = useCallback((message: WebSocketMessage) => {
    const progressMsg = message as DocumentProcessingProgressMessage;
    setDocuments(prev => prev.map(doc => 
      doc.id === progressMsg.data.document_id 
        ? { 
            ...doc, 
            processingProgress: progressMsg.data.progress * 100,
            processingMessage: progressMsg.data.message 
          }
        : doc
    ));
  }, []);

  const handleProcessingCompleted = useCallback((message: WebSocketMessage) => {
    const completedMsg = message as DocumentProcessingCompletedMessage;
    setDocuments(prev => prev.map(doc => 
      doc.id === completedMsg.data.document_id 
        ? { 
            ...doc, 
            status: 'completed',
            strategiesCount: completedMsg.data.strategies_count,
            processingProgress: 100,
            processingMessage: undefined
          }
        : doc
    ));
    setNotification({
      message: `Document processed successfully! ${completedMsg.data.strategies_count} strategies extracted.`,
      severity: 'success'
    });
  }, []);

  const handleProcessingFailed = useCallback((message: WebSocketMessage) => {
    const failedMsg = message as DocumentProcessingFailedMessage;
    setDocuments(prev => prev.map(doc => 
      doc.id === failedMsg.data.document_id 
        ? { 
            ...doc, 
            status: 'failed',
            processingProgress: undefined,
            processingMessage: undefined
          }
        : doc
    ));
    setNotification({
      message: `Document processing failed: ${failedMsg.data.error}`,
      severity: 'error'
    });
  }, []);

  const handleStrategyExtracted = useCallback((message: WebSocketMessage) => {
    const strategyMsg = message as StrategyExtractedMessage;
    setNotification({
      message: `Strategy extracted: ${strategyMsg.data.strategy_name}`,
      severity: 'info'
    });
  }, []);

  // Subscribe to WebSocket events
  useWebSocket('document.processing.progress', handleProcessingProgress);
  useWebSocket('document.processing.completed', handleProcessingCompleted);
  useWebSocket('document.processing.failed', handleProcessingFailed);
  useWebSocket('strategy.extracted', handleStrategyExtracted);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusColor = (status: Document['status']) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          setUploading(false);
          setUploadDialogOpen(false);
          setSelectedFile(null);
          return 100;
        }
        return prev + 10;
      });
    }, 300);
  };

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>, documentId: string) => {
    setMenuAnchor(event.currentTarget);
    setSelectedDocumentId(documentId);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedDocumentId(null);
  };

  const handleAction = (action: string) => {
    console.log(`${action} document:`, selectedDocumentId);
    handleMenuClose();
  };

  return (
    <Box>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ mb: 1, fontWeight: 600 }}>
            Documents
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Upload and manage your trading strategy documents
          </Typography>
        </Box>
        {canUploadDocuments && (
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setUploadDialogOpen(true)}
            size="large"
          >
            Upload Document
          </Button>
        )}
      </Box>

      {/* Statistics */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
                {documents.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Documents
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
                {documents.filter(d => d.status === 'processing').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Processing
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
                {documents.reduce((sum, d) => sum + d.strategiesCount, 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Strategies Extracted
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Documents List */}
      <Card>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            Recent Documents
          </Typography>
          {documents.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <DocumentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                No documents uploaded yet
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Upload your first trading document to get started
              </Typography>
              {canUploadDocuments && (
                <Button
                  variant="contained"
                  startIcon={<UploadIcon />}
                  onClick={() => setUploadDialogOpen(true)}
                >
                  Upload Document
                </Button>
              )}
            </Box>
          ) : (
            <List>
              {documents.map((document, index) => (
                <ListItem
                  key={document.id}
                  divider={index < documents.length - 1}
                  sx={{ px: 0 }}
                >
                  <ListItemAvatar>
                    <Avatar sx={{ bgcolor: 'primary.main' }}>
                      <DocumentIcon />
                    </Avatar>
                  </ListItemAvatar>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: 500 }}>
                          {document.name}
                        </Typography>
                        <Chip
                          label={document.status}
                          size="small"
                          color={getStatusColor(document.status)}
                          variant="outlined"
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" color="text.secondary">
                          {formatFileSize(document.size)} • Uploaded {formatDate(document.uploadedAt)}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          By {document.uploadedBy} • {document.strategiesCount} strategies extracted
                        </Typography>
                        {document.status === 'processing' && document.processingProgress !== undefined && (
                          <Box sx={{ mt: 1 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <LinearProgress 
                                variant="determinate" 
                                value={document.processingProgress} 
                                sx={{ flexGrow: 1, height: 6 }}
                              />
                              <Typography variant="caption" color="text.secondary">
                                {Math.round(document.processingProgress)}%
                              </Typography>
                            </Box>
                            {document.processingMessage && (
                              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                                {document.processingMessage}
                              </Typography>
                            )}
                          </Box>
                        )}
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <IconButton
                      edge="end"
                      onClick={(e) => handleMenuOpen(e, document.id)}
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
          View
        </MenuItem>
        <MenuItem onClick={() => handleAction('analyze')}>
          <AnalyzeIcon sx={{ mr: 2 }} />
          Re-analyze
        </MenuItem>
        <MenuItem onClick={() => handleAction('download')}>
          <DownloadIcon sx={{ mr: 2 }} />
          Download
        </MenuItem>
        <MenuItem onClick={() => handleAction('delete')} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 2 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Upload Dialog */}
      <Dialog
        open={uploadDialogOpen}
        onClose={() => !uploading && setUploadDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Upload Document</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="info" sx={{ mb: 3 }}>
              Supported formats: PDF, DOC, DOCX. Maximum file size: 100MB
            </Alert>
            
            <TextField
              type="file"
              fullWidth
              inputProps={{
                accept: '.pdf,.doc,.docx',
              }}
              onChange={handleFileSelect}
              disabled={uploading}
              sx={{ mb: 2 }}
            />
            
            {selectedFile && (
              <Box sx={{ mb: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                <Typography variant="subtitle2">Selected File:</Typography>
                <Typography variant="body2" color="text.secondary">
                  {selectedFile.name} ({formatFileSize(selectedFile.size)})
                </Typography>
              </Box>
            )}
            
            {uploading && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Uploading... {uploadProgress}%
                </Typography>
                <LinearProgress variant="determinate" value={uploadProgress} />
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => setUploadDialogOpen(false)}
            disabled={uploading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            variant="contained"
          >
            {uploading ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={notification !== null}
        autoHideDuration={6000}
        onClose={() => setNotification(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        {notification && (
          <Alert 
            onClose={() => setNotification(null)} 
            severity={notification.severity}
            sx={{ width: '100%' }}
            icon={
              notification.severity === 'success' ? <CheckIcon /> : 
              notification.severity === 'error' ? <ErrorIcon /> : undefined
            }
          >
            {notification.message}
          </Alert>
        )}
      </Snackbar>
    </Box>
  );
};

export default DocumentsPage;