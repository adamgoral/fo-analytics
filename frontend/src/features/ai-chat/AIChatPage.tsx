import React, { useState, useEffect } from 'react';
import { Box, Paper, Typography, Divider } from '@mui/material';
import ChatSidebar from './ChatSidebar';
import ChatInterface from './ChatInterface';
import { useAppDispatch, useAppSelector } from '../../store';
import { fetchMessages } from '../../store/slices/chatSlice';

const AIChatPage: React.FC = () => {
  const dispatch = useAppDispatch();
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const { currentSession } = useAppSelector((state) => state.chat);

  useEffect(() => {
    if (selectedSessionId) {
      dispatch(fetchMessages({ sessionId: selectedSessionId }));
    }
  }, [selectedSessionId, dispatch]);

  const handleSessionSelect = (sessionId: string) => {
    setSelectedSessionId(sessionId);
  };

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 64px)' }}>
      {/* Sidebar */}
      <Paper
        elevation={0}
        sx={{
          borderRight: 1,
          borderColor: 'divider',
          height: '100%',
        }}
      >
        <ChatSidebar onSessionSelect={handleSessionSelect} />
      </Paper>

      {/* Main Chat Area */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {selectedSessionId && currentSession ? (
          <ChatInterface sessionId={selectedSessionId} />
        ) : (
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              p: 4,
            }}
          >
            <Box sx={{ textAlign: 'center', maxWidth: 600 }}>
              <Typography variant="h4" gutterBottom color="text.secondary">
                Welcome to AI Chat Assistant
              </Typography>
              <Typography variant="body1" color="text.secondary" paragraph>
                Select a chat session from the sidebar or create a new one to start chatting
                with our AI assistant. You can ask questions about documents, strategies,
                backtests, or get help with portfolio optimization.
              </Typography>
              <Typography variant="body2" color="text.secondary">
                The AI assistant has access to your uploaded documents and can help you
                extract insights, develop trading strategies, and analyze results.
              </Typography>
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default AIChatPage;