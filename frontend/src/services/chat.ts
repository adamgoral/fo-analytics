import { apiClient } from './api';

// Temporary workaround - define PaginatedResponse locally
interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// Types for chat functionality
export interface ChatSession {
  id: string;
  user_id: string;
  name: string;
  context_type?: 'general' | 'document' | 'strategy' | 'backtest' | 'portfolio';
  context_id?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: {
    tokens_used?: number;
    model?: string;
    error?: string;
  };
  created_at: string;
}

export interface CreateChatSessionRequest {
  name: string;
  context_type?: 'general' | 'document' | 'strategy' | 'backtest' | 'portfolio';
  context_id?: string;
}

export interface UpdateChatSessionRequest {
  name?: string;
  metadata?: Record<string, any>;
}

export interface CreateChatMessageRequest {
  content: string;
  stream?: boolean;
}

export interface ChatMessageResponse {
  message: ChatMessage;
  session: ChatSession;
}

// API service for chat functionality
export const chatService = {
  // Session management
  async createSession(data: CreateChatSessionRequest): Promise<ChatSession> {
    const response = await apiClient.post<ChatSession>('/api/v1/chat/sessions', data);
    return response.data;
  },

  async getSessions(skip = 0, limit = 20): Promise<PaginatedResponse<ChatSession>> {
    const response = await apiClient.get<PaginatedResponse<ChatSession>>('/api/v1/chat/sessions', {
      params: { skip, limit },
    });
    return response.data;
  },

  async getSession(sessionId: string): Promise<ChatSession> {
    const response = await apiClient.get<ChatSession>(`/api/v1/chat/sessions/${sessionId}`);
    return response.data;
  },

  async updateSession(sessionId: string, data: UpdateChatSessionRequest): Promise<ChatSession> {
    const response = await apiClient.patch<ChatSession>(`/api/v1/chat/sessions/${sessionId}`, data);
    return response.data;
  },

  async deleteSession(sessionId: string): Promise<void> {
    await apiClient.delete(`/api/v1/chat/sessions/${sessionId}`);
  },

  // Message management
  async getMessages(sessionId: string, skip = 0, limit = 50): Promise<PaginatedResponse<ChatMessage>> {
    const response = await apiClient.get<PaginatedResponse<ChatMessage>>(
      `/api/v1/chat/sessions/${sessionId}/messages`,
      { params: { skip, limit } }
    );
    return response.data;
  },

  async sendMessage(
    sessionId: string,
    data: CreateChatMessageRequest
  ): Promise<ChatMessage> {
    const response = await apiClient.post<ChatMessage>(
      `/api/v1/chat/sessions/${sessionId}/messages`,
      data
    );
    return response.data;
  },

  // Streaming support for AI responses
  async sendMessageStream(
    sessionId: string,
    content: string,
    onMessage: (message: string) => void,
    onComplete: (finalMessage: ChatMessage) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    try {
      const response = await fetch(`${apiClient.defaults.baseURL}/api/v1/chat/sessions/${sessionId}/messages/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({ content, stream: true }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              continue;
            }
            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                onMessage(parsed.content);
              } else if (parsed.message) {
                onComplete(parsed.message);
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      onError(error as Error);
    }
  },
};