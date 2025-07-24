import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress,
  Avatar,
  Chip,
  Menu,
  MenuItem,
  Tooltip,
} from '@mui/material';
import {
  Send as SendIcon,
  SmartToy as AiIcon,
  Person as PersonIcon,
  MoreVert as MoreIcon,
  Description as DocumentIcon,
  TrendingUp as StrategyIcon,
  Assessment as BacktestIcon,
  AccountBalance as PortfolioIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useAppDispatch, useAppSelector } from '../../store';
import {
  sendMessage,
  setStreamingMessage,
  appendStreamingMessage,
  addMessage,
} from '../../store/slices/chatSlice';
import { chatService } from '../../services/chat';

interface ChatInterfaceProps {
  sessionId: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ sessionId }) => {
  const dispatch = useAppDispatch();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [input, setInput] = useState('');
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const { messages, currentSession, isSending, streamingMessage } = useAppSelector(
    (state) => state.chat
  );
  const sessionMessages = messages[sessionId] || [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [sessionMessages, streamingMessage]);

  const handleSend = async () => {
    if (!input.trim() || isSending) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message immediately
    const tempUserMessage = {
      id: `temp-${Date.now()}`,
      session_id: sessionId,
      role: 'user' as const,
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    dispatch(addMessage({ sessionId, message: tempUserMessage }));

    // Send message with streaming
    dispatch(setStreamingMessage(''));
    
    await chatService.sendMessageStream(
      sessionId,
      userMessage,
      (chunk) => {
        dispatch(appendStreamingMessage(chunk));
      },
      (finalMessage) => {
        dispatch(setStreamingMessage(null));
        dispatch(addMessage({ sessionId, message: finalMessage }));
      },
      (error) => {
        console.error('Stream error:', error);
        dispatch(setStreamingMessage(null));
        // Add error message
        const errorMessage = {
          id: `error-${Date.now()}`,
          session_id: sessionId,
          role: 'assistant' as const,
          content: 'Sorry, I encountered an error processing your message. Please try again.',
          metadata: { error: error.message },
          created_at: new Date().toISOString(),
        };
        dispatch(addMessage({ sessionId, message: errorMessage }));
      }
    );
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getContextIcon = () => {
    if (!currentSession?.context_type) return null;

    const iconMap = {
      document: <DocumentIcon />,
      strategy: <StrategyIcon />,
      backtest: <BacktestIcon />,
      portfolio: <PortfolioIcon />,
    };

    return iconMap[currentSession.context_type] || null;
  };

  const getContextLabel = () => {
    if (!currentSession?.context_type) return null;

    return (
      <Chip
        size="small"
        icon={getContextIcon()}
        label={currentSession.context_type}
        color="primary"
        variant="outlined"
      />
    );
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6">{currentSession?.name || 'Chat'}</Typography>
          {getContextLabel()}
        </Box>
        <IconButton
          size="small"
          onClick={(e) => setAnchorEl(e.currentTarget)}
        >
          <MoreIcon />
        </IconButton>
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={() => setAnchorEl(null)}
        >
          <MenuItem onClick={() => setAnchorEl(null)}>Clear History</MenuItem>
          <MenuItem onClick={() => setAnchorEl(null)}>Export Chat</MenuItem>
        </Menu>
      </Box>

      {/* Messages */}
      <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
        <List sx={{ p: 0 }}>
          {sessionMessages.map((message, index) => (
            <React.Fragment key={message.id}>
              <ListItem
                sx={{
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  py: 2,
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 1,
                    width: '100%',
                  }}
                >
                  <Avatar
                    sx={{
                      width: 32,
                      height: 32,
                      bgcolor: message.role === 'user' ? 'primary.main' : 'secondary.main',
                    }}
                  >
                    {message.role === 'user' ? <PersonIcon /> : <AiIcon />}
                  </Avatar>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    {message.role === 'user' ? 'You' : 'AI Assistant'}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {format(new Date(message.created_at), 'HH:mm')}
                  </Typography>
                  {message.metadata?.tokens_used && (
                    <Tooltip title="Tokens used">
                      <Chip
                        size="small"
                        label={`${message.metadata.tokens_used} tokens`}
                        variant="outlined"
                        sx={{ ml: 'auto' }}
                      />
                    </Tooltip>
                  )}
                </Box>
                <Box sx={{ pl: 5, width: '100%' }}>
                  <Typography
                    variant="body1"
                    sx={{
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {message.content}
                  </Typography>
                </Box>
              </ListItem>
              {index < sessionMessages.length - 1 && <Divider />}
            </React.Fragment>
          ))}
          
          {/* Streaming message */}
          {streamingMessage !== null && (
            <>
              <Divider />
              <ListItem
                sx={{
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  py: 2,
                }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1,
                    mb: 1,
                    width: '100%',
                  }}
                >
                  <Avatar
                    sx={{
                      width: 32,
                      height: 32,
                      bgcolor: 'secondary.main',
                    }}
                  >
                    <AiIcon />
                  </Avatar>
                  <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                    AI Assistant
                  </Typography>
                  <CircularProgress size={16} sx={{ ml: 1 }} />
                </Box>
                <Box sx={{ pl: 5, width: '100%' }}>
                  <Typography
                    variant="body1"
                    sx={{
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {streamingMessage || '...'}
                  </Typography>
                </Box>
              </ListItem>
            </>
          )}
        </List>
        <div ref={messagesEndRef} />
      </Box>

      {/* Input */}
      <Paper
        elevation={3}
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
        }}
      >
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isSending || streamingMessage !== null}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
              },
            }}
          />
          <IconButton
            color="primary"
            onClick={handleSend}
            disabled={!input.trim() || isSending || streamingMessage !== null}
            sx={{
              bgcolor: 'primary.main',
              color: 'white',
              '&:hover': {
                bgcolor: 'primary.dark',
              },
              '&:disabled': {
                bgcolor: 'action.disabledBackground',
              },
            }}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Paper>
    </Box>
  );
};

export default ChatInterface;