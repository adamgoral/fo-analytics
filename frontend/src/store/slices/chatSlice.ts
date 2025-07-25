import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { chatService } from '../../services/chat';
import type { ChatSession, ChatMessage, CreateChatSessionRequest } from '../../services/chat';

interface ChatState {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  messages: Record<string, ChatMessage[]>; // sessionId -> messages
  isLoading: boolean;
  isLoadingMessages: boolean;
  isSending: boolean;
  error: string | null;
  streamingMessage: string | null;
  totalSessions: number;
}

const initialState: ChatState = {
  sessions: [],
  currentSession: null,
  messages: {},
  isLoading: false,
  isLoadingMessages: false,
  isSending: false,
  error: null,
  streamingMessage: null,
  totalSessions: 0,
};

// Async thunks
export const fetchSessions = createAsyncThunk(
  'chat/fetchSessions',
  async ({ skip = 0, limit = 20 }: { skip?: number; limit?: number }) => {
    const response = await chatService.getSessions(skip, limit);
    return response;
  }
);

export const createSession = createAsyncThunk(
  'chat/createSession',
  async (data: CreateChatSessionRequest) => {
    const session = await chatService.createSession(data);
    return session;
  }
);

export const selectSession = createAsyncThunk(
  'chat/selectSession',
  async (sessionId: string) => {
    const session = await chatService.getSession(sessionId);
    return session;
  }
);

export const fetchMessages = createAsyncThunk(
  'chat/fetchMessages',
  async ({ sessionId, skip = 0, limit = 50 }: { sessionId: string; skip?: number; limit?: number }) => {
    const response = await chatService.getMessages(sessionId, skip, limit);
    return { sessionId, messages: response.items };
  }
);

export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async ({ sessionId, content }: { sessionId: string; content: string }) => {
    const message = await chatService.sendMessage(sessionId, { content, stream: false });
    return message;
  }
);

export const deleteSession = createAsyncThunk(
  'chat/deleteSession',
  async (sessionId: string) => {
    await chatService.deleteSession(sessionId);
    return sessionId;
  }
);

// Chat slice
const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setStreamingMessage: (state, action: PayloadAction<string | null>) => {
      state.streamingMessage = action.payload;
    },
    appendStreamingMessage: (state, action: PayloadAction<string>) => {
      if (state.streamingMessage) {
        state.streamingMessage += action.payload;
      } else {
        state.streamingMessage = action.payload;
      }
    },
    addMessage: (state, action: PayloadAction<{ sessionId: string; message: ChatMessage }>) => {
      const { sessionId, message } = action.payload;
      if (!state.messages[sessionId]) {
        state.messages[sessionId] = [];
      }
      state.messages[sessionId].push(message);
    },
    clearError: (state) => {
      state.error = null;
    },
    clearCurrentSession: (state) => {
      state.currentSession = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch sessions
    builder
      .addCase(fetchSessions.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchSessions.fulfilled, (state, action) => {
        state.isLoading = false;
        state.sessions = action.payload.items;
        state.totalSessions = action.payload.total;
      })
      .addCase(fetchSessions.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to fetch sessions';
      });

    // Create session
    builder
      .addCase(createSession.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(createSession.fulfilled, (state, action) => {
        state.isLoading = false;
        state.sessions.unshift(action.payload);
        state.currentSession = action.payload;
        state.messages[action.payload.id] = [];
      })
      .addCase(createSession.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to create session';
      });

    // Select session
    builder
      .addCase(selectSession.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(selectSession.fulfilled, (state, action) => {
        state.isLoading = false;
        state.currentSession = action.payload;
      })
      .addCase(selectSession.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.error.message || 'Failed to select session';
      });

    // Fetch messages
    builder
      .addCase(fetchMessages.pending, (state) => {
        state.isLoadingMessages = true;
        state.error = null;
      })
      .addCase(fetchMessages.fulfilled, (state, action) => {
        state.isLoadingMessages = false;
        state.messages[action.payload.sessionId] = action.payload.messages;
      })
      .addCase(fetchMessages.rejected, (state, action) => {
        state.isLoadingMessages = false;
        state.error = action.error.message || 'Failed to fetch messages';
      });

    // Send message
    builder
      .addCase(sendMessage.pending, (state) => {
        state.isSending = true;
        state.error = null;
        state.streamingMessage = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isSending = false;
        const sessionId = action.payload.session_id;
        if (!state.messages[sessionId]) {
          state.messages[sessionId] = [];
        }
        state.messages[sessionId].push(action.payload);
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isSending = false;
        state.error = action.error.message || 'Failed to send message';
      });

    // Delete session
    builder
      .addCase(deleteSession.fulfilled, (state, action) => {
        const sessionId = action.payload;
        state.sessions = state.sessions.filter((s) => s.id !== sessionId);
        delete state.messages[sessionId];
        if (state.currentSession?.id === sessionId) {
          state.currentSession = null;
        }
      });
  },
});

export const {
  setStreamingMessage,
  appendStreamingMessage,
  addMessage,
  clearError,
  clearCurrentSession,
} = chatSlice.actions;

export default chatSlice.reducer;