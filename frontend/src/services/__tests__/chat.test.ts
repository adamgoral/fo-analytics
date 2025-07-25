import { describe, it, expect, vi, beforeEach } from 'vitest';
import { chatService } from '../chat';
import { apiClient } from '../api';

// Mock the apiClient
vi.mock('../api', () => ({
  apiClient: {
    post: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
    defaults: {
      baseURL: 'http://localhost:8000/api/v1',
    },
  },
}));

// Mock fetch for streaming
global.fetch = vi.fn();

describe('chatService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Session Management', () => {
    it('should create a new chat session', async () => {
      const mockSession = {
        id: '123',
        user_id: 'user123',
        title: 'Test Chat',
        context_type: 'general',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      (apiClient.post as any).mockResolvedValueOnce({ data: mockSession });

      const result = await chatService.createSession({
        title: 'Test Chat',
        context_type: 'general',
      });

      expect(apiClient.post).toHaveBeenCalledWith('/chat/sessions', {
        title: 'Test Chat',
        context_type: 'general',
      });
      expect(result).toEqual(mockSession);
    });

    it('should get all sessions with pagination', async () => {
      const mockResponse = {
        items: [
          { id: '1', title: 'Chat 1' },
          { id: '2', title: 'Chat 2' },
        ],
        total: 2,
        skip: 0,
        limit: 20,
      };

      (apiClient.get as any).mockResolvedValueOnce({ data: mockResponse });

      const result = await chatService.getSessions(0, 20);

      expect(apiClient.get).toHaveBeenCalledWith('/chat/sessions', {
        params: { skip: 0, limit: 20 },
      });
      expect(result).toEqual(mockResponse);
    });

    it('should get a specific session', async () => {
      const mockSession = { id: '123', title: 'Test Chat' };
      (apiClient.get as any).mockResolvedValueOnce({ data: mockSession });

      const result = await chatService.getSession('123');

      expect(apiClient.get).toHaveBeenCalledWith('/chat/sessions/123');
      expect(result).toEqual(mockSession);
    });

    it('should update a session', async () => {
      const mockUpdatedSession = { id: '123', title: 'Updated Chat' };
      (apiClient.patch as any).mockResolvedValueOnce({ data: mockUpdatedSession });

      const result = await chatService.updateSession('123', { title: 'Updated Chat' });

      expect(apiClient.patch).toHaveBeenCalledWith('/chat/sessions/123', {
        title: 'Updated Chat',
      });
      expect(result).toEqual(mockUpdatedSession);
    });

    it('should delete a session', async () => {
      (apiClient.delete as any).mockResolvedValueOnce({});

      await chatService.deleteSession('123');

      expect(apiClient.delete).toHaveBeenCalledWith('/chat/sessions/123');
    });
  });

  describe('Message Management', () => {
    it('should get messages for a session', async () => {
      const mockMessages = {
        items: [
          { id: '1', content: 'Hello', role: 'user' },
          { id: '2', content: 'Hi there!', role: 'assistant' },
        ],
        total: 2,
        skip: 0,
        limit: 50,
      };

      (apiClient.get as any).mockResolvedValueOnce({ data: mockMessages });

      const result = await chatService.getMessages('session123', 0, 50);

      expect(apiClient.get).toHaveBeenCalledWith(
        '/chat/sessions/session123/messages',
        { params: { skip: 0, limit: 50 } }
      );
      expect(result).toEqual(mockMessages);
    });

    it('should send a message', async () => {
      const mockMessage = {
        id: 'msg123',
        session_id: 'session123',
        content: 'Test message',
        role: 'user',
        created_at: '2024-01-01T00:00:00Z',
      };

      (apiClient.post as any).mockResolvedValueOnce({ data: mockMessage });

      const result = await chatService.sendMessage('session123', {
        content: 'Test message',
        stream: false,
      });

      expect(apiClient.post).toHaveBeenCalledWith(
        '/chat/sessions/session123/messages',
        { content: 'Test message', stream: false }
      );
      expect(result).toEqual(mockMessage);
    });
  });

  describe('Streaming', () => {
    it('should handle streaming messages', async () => {
      const mockResponse = {
        ok: true,
        body: {
          getReader: () => ({
            read: vi.fn()
              .mockResolvedValueOnce({
                done: false,
                value: new TextEncoder().encode('data: {"content": "Hello"}\n\n'),
              })
              .mockResolvedValueOnce({
                done: false,
                value: new TextEncoder().encode('data: {"content": " world"}\n\n'),
              })
              .mockResolvedValueOnce({
                done: false,
                value: new TextEncoder().encode('data: {"message": {"id": "123", "content": "Hello world"}}\n\n'),
              })
              .mockResolvedValueOnce({ done: true }),
          }),
        },
      };

      (global.fetch as any).mockResolvedValueOnce(mockResponse);

      const messages: string[] = [];
      let finalMessage: any = null;

      await chatService.sendMessageStream(
        'session123',
        'Test',
        (msg) => messages.push(msg),
        (msg) => { finalMessage = msg; },
        () => {}
      );

      expect(messages).toEqual(['Hello', ' world']);
      expect(finalMessage).toEqual({ id: '123', content: 'Hello world' });
    });

    it('should handle streaming errors', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      let error: Error | null = null;

      await chatService.sendMessageStream(
        'session123',
        'Test',
        () => {},
        () => {},
        (err) => { error = err; }
      );

      expect(error?.message).toBe('Network error');
    });

    it('should handle non-ok responses', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      let error: Error | null = null;

      await chatService.sendMessageStream(
        'session123',
        'Test',
        () => {},
        () => {},
        (err) => { error = err; }
      );

      expect(error?.message).toBe('HTTP error! status: 500');
    });
  });
});