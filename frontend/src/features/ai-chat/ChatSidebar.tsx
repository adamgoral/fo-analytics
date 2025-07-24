import React, { useState } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  IconButton,
  Typography,
  TextField,
  Button,
  Divider,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  Skeleton,
} from '@mui/material';
import {
  Add as AddIcon,
  Chat as ChatIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  MoreVert as MoreIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useAppDispatch, useAppSelector } from '../../store';
import {
  fetchSessions,
  createSession,
  selectSession,
  deleteSession,
} from '../../store/slices/chatSlice';
import { ChatSession } from '../../services/chat';

interface ChatSidebarProps {
  onSessionSelect: (sessionId: string) => void;
}

const ChatSidebar: React.FC<ChatSidebarProps> = ({ onSessionSelect }) => {
  const dispatch = useAppDispatch();
  const { sessions, currentSession, isLoading } = useAppSelector((state) => state.chat);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [menuAnchor, setMenuAnchor] = useState<{
    element: HTMLElement | null;
    session: ChatSession | null;
  }>({ element: null, session: null });
  const [newChatDialog, setNewChatDialog] = useState(false);
  const [newChatData, setNewChatData] = useState({
    name: '',
    context_type: 'general' as const,
  });

  React.useEffect(() => {
    dispatch(fetchSessions({ skip: 0, limit: 50 }));
  }, [dispatch]);

  const handleCreateChat = async () => {
    if (!newChatData.name.trim()) return;
    
    const result = await dispatch(createSession({
      name: newChatData.name,
      context_type: newChatData.context_type,
    }));
    
    if (createSession.fulfilled.match(result)) {
      setNewChatDialog(false);
      setNewChatData({ name: '', context_type: 'general' });
      onSessionSelect(result.payload.id);
    }
  };

  const handleSelectSession = async (session: ChatSession) => {
    await dispatch(selectSession(session.id));
    onSessionSelect(session.id);
  };

  const handleDeleteSession = async (sessionId: string) => {
    await dispatch(deleteSession(sessionId));
    setMenuAnchor({ element: null, session: null });
  };

  const filteredSessions = sessions.filter((session) =>
    session.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Box sx={{ width: 320, height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">Chat Sessions</Typography>
          <Button
            startIcon={<AddIcon />}
            variant="contained"
            size="small"
            onClick={() => setNewChatDialog(true)}
          >
            New Chat
          </Button>
        </Box>
        
        {/* Search */}
        <TextField
          fullWidth
          size="small"
          placeholder="Search sessions..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ color: 'action.active', mr: 1 }} />,
          }}
        />
      </Box>

      <Divider />

      {/* Sessions List */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {isLoading ? (
          <Box sx={{ p: 2 }}>
            {[...Array(5)].map((_, i) => (
              <Skeleton key={i} height={72} sx={{ mb: 1 }} />
            ))}
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {filteredSessions.map((session) => (
              <ListItem
                key={session.id}
                disablePadding
                secondaryAction={
                  <IconButton
                    edge="end"
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      setMenuAnchor({ element: e.currentTarget, session });
                    }}
                  >
                    <MoreIcon />
                  </IconButton>
                }
                sx={{
                  bgcolor: currentSession?.id === session.id ? 'action.selected' : 'transparent',
                }}
              >
                <ListItemButton onClick={() => handleSelectSession(session)}>
                  <ListItemIcon>
                    <ChatIcon />
                  </ListItemIcon>
                  <ListItemText
                    primary={session.name}
                    secondary={
                      <Box>
                        <Typography variant="caption" display="block">
                          {session.context_type || 'General'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {format(new Date(session.updated_at), 'MMM d, yyyy HH:mm')}
                        </Typography>
                      </Box>
                    }
                    primaryTypographyProps={{
                      noWrap: true,
                      sx: { fontWeight: currentSession?.id === session.id ? 600 : 400 },
                    }}
                  />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        )}
      </Box>

      {/* Context Menu */}
      <Menu
        anchorEl={menuAnchor.element}
        open={Boolean(menuAnchor.element)}
        onClose={() => setMenuAnchor({ element: null, session: null })}
      >
        <MenuItem onClick={() => {
          // TODO: Implement rename
          setMenuAnchor({ element: null, session: null });
        }}>
          <ListItemIcon>
            <EditIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Rename</ListItemText>
        </MenuItem>
        <MenuItem
          onClick={() => {
            if (menuAnchor.session) {
              handleDeleteSession(menuAnchor.session.id);
            }
          }}
        >
          <ListItemIcon>
            <DeleteIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText>Delete</ListItemText>
        </MenuItem>
      </Menu>

      {/* New Chat Dialog */}
      <Dialog
        open={newChatDialog}
        onClose={() => setNewChatDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Chat Session</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Session Name"
              fullWidth
              value={newChatData.name}
              onChange={(e) => setNewChatData({ ...newChatData, name: e.target.value })}
              autoFocus
            />
            <FormControl fullWidth>
              <InputLabel>Context Type</InputLabel>
              <Select
                value={newChatData.context_type}
                label="Context Type"
                onChange={(e) => setNewChatData({
                  ...newChatData,
                  context_type: e.target.value as any,
                })}
              >
                <MenuItem value="general">General</MenuItem>
                <MenuItem value="document">Document Analysis</MenuItem>
                <MenuItem value="strategy">Strategy Development</MenuItem>
                <MenuItem value="backtest">Backtest Analysis</MenuItem>
                <MenuItem value="portfolio">Portfolio Optimization</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewChatDialog(false)}>Cancel</Button>
          <Button
            onClick={handleCreateChat}
            variant="contained"
            disabled={!newChatData.name.trim()}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ChatSidebar;