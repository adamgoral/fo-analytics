import { describe, it, expect, vi, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';
import chatReducer, {
  fetchSessions,
  createSession,
  selectSession,
  fetchMessages,
  sendMessage,
  deleteSession,
  setStreamingMessage,
  appendStreamingMessage,
  addMessage,
  clearError,
  clearCurrentSession,
} from '../chatSlice';
import { chatService } from '../../../services/chat';

// Mock the chat service
vi.mock('../../../services/chat', () => ({
  chatService: {
    getSessions: vi.fn(),
    createSession: vi.fn(),
    getSession: vi.fn(),
    getMessages: vi.fn(),
    sendMessage: vi.fn(),
    deleteSession: vi.fn(),
  },
}));

describe('chatSlice', () => {
  let store: any;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        chat: chatReducer,
      },
    });
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = store.getState().chat;
      expect(state).toEqual({
        sessions: [],
        currentSession: null,
        messages: {},
        isLoading: false,
        isLoadingMessages: false,
        isSending: false,
        error: null,
        streamingMessage: null,
        totalSessions: 0,
      });
    });
  });

  describe('Synchronous Actions', () => {
    it('should set streaming message', () => {
      store.dispatch(setStreamingMessage('Hello'));
      expect(store.getState().chat.streamingMessage).toBe('Hello');

      store.dispatch(setStreamingMessage(null));
      expect(store.getState().chat.streamingMessage).toBe(null);
    });

    it('should append to streaming message', () => {
      store.dispatch(setStreamingMessage('Hello'));
      store.dispatch(appendStreamingMessage(' world'));
      expect(store.getState().chat.streamingMessage).toBe('Hello world');
    });

    it('should add a message to the correct session', () => {
      const message = {
        id: '1',
        session_id: 'session1',
        role: 'user' as const,
        content: 'Test',
        created_at: '2024-01-01',
      };

      store.dispatch(addMessage({ sessionId: 'session1', message }));
      expect(store.getState().chat.messages.session1).toEqual([message]);
    });

    it('should clear error', () => {
      // First set an error
      store = configureStore({
        reducer: {
          chat: chatReducer,
        },
        preloadedState: {
          chat: {
            sessions: [],
            currentSession: null,
            messages: {},
            isLoading: false,
            isLoadingMessages: false,
            isSending: false,
            error: 'Test error',
            streamingMessage: null,
            totalSessions: 0,
          },
        },
      });

      store.dispatch(clearError());
      expect(store.getState().chat.error).toBe(null);
    });

    it('should clear current session', () => {
      store = configureStore({
        reducer: {
          chat: chatReducer,
        },
        preloadedState: {
          chat: {
            sessions: [],
            currentSession: { id: '1', name: 'Test' },
            messages: {},
            isLoading: false,
            isLoadingMessages: false,
            isSending: false,
            error: null,
            streamingMessage: null,
            totalSessions: 0,
          },
        },
      });

      store.dispatch(clearCurrentSession());
      expect(store.getState().chat.currentSession).toBe(null);
    });
  });

  describe('Async Actions', () => {
    describe('fetchSessions', () => {
      it('should fetch sessions successfully', async () => {
        const mockResponse = {
          items: [
            { id: '1', name: 'Chat 1' },
            { id: '2', name: 'Chat 2' },
          ],
          total: 2,
        };

        (chatService.getSessions as any).mockResolvedValueOnce(mockResponse);

        await store.dispatch(fetchSessions({ skip: 0, limit: 20 }));

        const state = store.getState().chat;
        expect(state.sessions).toEqual(mockResponse.items);
        expect(state.totalSessions).toBe(2);
        expect(state.isLoading).toBe(false);
        expect(state.error).toBe(null);
      });

      it('should handle fetch sessions error', async () => {
        (chatService.getSessions as any).mockRejectedValueOnce(new Error('Network error'));

        await store.dispatch(fetchSessions({ skip: 0, limit: 20 }));

        const state = store.getState().chat;
        expect(state.sessions).toEqual([]);
        expect(state.isLoading).toBe(false);
        expect(state.error).toBe('Network error');
      });
    });

    describe('createSession', () => {
      it('should create a session successfully', async () => {
        const newSession = {
          id: '123',
          name: 'New Chat',
          user_id: 'user1',
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        };

        (chatService.createSession as any).mockResolvedValueOnce(newSession);

        await store.dispatch(createSession({ name: 'New Chat' }));

        const state = store.getState().chat;
        expect(state.sessions).toContainEqual(newSession);
        expect(state.currentSession).toEqual(newSession);
        expect(state.messages['123']).toEqual([]);
        expect(state.isLoading).toBe(false);
      });

      it('should handle create session error', async () => {
        (chatService.createSession as any).mockRejectedValueOnce(new Error('Creation failed'));

        await store.dispatch(createSession({ name: 'New Chat' }));

        const state = store.getState().chat;
        expect(state.isLoading).toBe(false);
        expect(state.error).toBe('Creation failed');
      });
    });

    describe('selectSession', () => {
      it('should select a session successfully', async () => {
        const session = { id: '123', name: 'Selected Chat' };
        (chatService.getSession as any).mockResolvedValueOnce(session);

        await store.dispatch(selectSession('123'));

        const state = store.getState().chat;
        expect(state.currentSession).toEqual(session);
        expect(state.isLoading).toBe(false);
      });
    });

    describe('fetchMessages', () => {
      it('should fetch messages successfully', async () => {
        const messages = [
          { id: '1', content: 'Hello' },
          { id: '2', content: 'World' },
        ];

        (chatService.getMessages as any).mockResolvedValueOnce({ items: messages });

        await store.dispatch(fetchMessages({ sessionId: 'session1' }));

        const state = store.getState().chat;
        expect(state.messages.session1).toEqual(messages);
        expect(state.isLoadingMessages).toBe(false);
      });
    });

    describe('sendMessage', () => {
      it('should send a message successfully', async () => {
        const newMessage = {
          id: 'msg1',
          session_id: 'session1',
          content: 'Test message',
          role: 'user',
          created_at: '2024-01-01',
        };

        (chatService.sendMessage as any).mockResolvedValueOnce(newMessage);

        await store.dispatch(sendMessage({ sessionId: 'session1', content: 'Test message' }));

        const state = store.getState().chat;
        expect(state.messages.session1).toContainEqual(newMessage);
        expect(state.isSending).toBe(false);
        expect(state.streamingMessage).toBe(null);
      });
    });

    describe('deleteSession', () => {
      it('should delete a session successfully', async () => {
        // Setup initial state with sessions
        store = configureStore({
          reducer: {
            chat: chatReducer,
          },
          preloadedState: {
            chat: {
              sessions: [
                { id: '1', name: 'Chat 1' },
                { id: '2', name: 'Chat 2' },
              ],
              currentSession: { id: '1', name: 'Chat 1' },
              messages: {
                '1': [{ id: 'msg1', content: 'Test' }],
                '2': [],
              },
              isLoading: false,
              isLoadingMessages: false,
              isSending: false,
              error: null,
              streamingMessage: null,
              totalSessions: 2,
            },
          },
        });

        (chatService.deleteSession as any).mockResolvedValueOnce(undefined);

        await store.dispatch(deleteSession('1'));

        const state = store.getState().chat;
        expect(state.sessions).toHaveLength(1);
        expect(state.sessions[0].id).toBe('2');
        expect(state.messages['1']).toBeUndefined();
        expect(state.currentSession).toBe(null);
      });
    });
  });
});