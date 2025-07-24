import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import ChatInterface from '../ChatInterface';
import chatReducer from '../../../store/slices/chatSlice';
import { chatService } from '../../../services/chat';

// Mock the chat service
vi.mock('../../../services/chat', () => ({
  chatService: {
    sendMessageStream: vi.fn(),
  },
}));

// Mock date-fns format
vi.mock('date-fns', () => ({
  format: vi.fn(() => '10:30'),
}));

const mockMessages = [
  {
    id: '1',
    session_id: 'session1',
    role: 'user',
    content: 'Hello, can you help me?',
    created_at: '2024-01-01T10:30:00Z',
  },
  {
    id: '2',
    session_id: 'session1',
    role: 'assistant',
    content: 'Of course! I\'d be happy to help.',
    created_at: '2024-01-01T10:31:00Z',
    metadata: {
      tokens_used: 15,
    },
  },
];

const mockSession = {
  id: 'session1',
  name: 'Test Chat',
  context_type: 'document',
};

describe('ChatInterface', () => {
  let store: any;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        chat: chatReducer,
      },
      preloadedState: {
        chat: {
          sessions: [mockSession],
          currentSession: mockSession,
          messages: {
            session1: mockMessages,
          },
          isLoading: false,
          isLoadingMessages: false,
          isSending: false,
          error: null,
          streamingMessage: null,
          totalSessions: 1,
        },
      },
    });
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <Provider store={store}>
        <ChatInterface sessionId="session1" />
      </Provider>
    );
  };

  it('should render chat header with session info', () => {
    renderComponent();

    expect(screen.getByText('Test Chat')).toBeInTheDocument();
    expect(screen.getByText('document')).toBeInTheDocument();
  });

  it('should display messages correctly', () => {
    renderComponent();

    expect(screen.getByText('Hello, can you help me?')).toBeInTheDocument();
    expect(screen.getByText('Of course! I\'d be happy to help.')).toBeInTheDocument();
    expect(screen.getByText('You')).toBeInTheDocument();
    expect(screen.getByText('AI Assistant')).toBeInTheDocument();
  });

  it('should show token usage when available', () => {
    renderComponent();

    expect(screen.getByText('15 tokens')).toBeInTheDocument();
  });

  it('should handle message input', () => {
    renderComponent();

    const input = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(input, { target: { value: 'Test message' } });

    expect(input).toHaveValue('Test message');
  });

  it('should send message on button click', async () => {
    (chatService.sendMessageStream as any).mockImplementation(
      async (sessionId, content, onMessage, onComplete) => {
        onMessage('This is ');
        onMessage('a response.');
        onComplete({
          id: '3',
          session_id: sessionId,
          role: 'assistant',
          content: 'This is a response.',
          created_at: '2024-01-01T10:32:00Z',
        });
      }
    );

    renderComponent();

    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByTestId('SendIcon').closest('button');

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton!);

    await waitFor(() => {
      expect(chatService.sendMessageStream).toHaveBeenCalledWith(
        'session1',
        'Test message',
        expect.any(Function),
        expect.any(Function),
        expect.any(Function)
      );
    });

    expect(input).toHaveValue('');
  });

  it('should send message on Enter key press', async () => {
    renderComponent();

    const input = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter', shiftKey: false });

    await waitFor(() => {
      expect(chatService.sendMessageStream).toHaveBeenCalled();
    });
  });

  it('should not send message on Shift+Enter', () => {
    renderComponent();

    const input = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter', shiftKey: true });

    expect(chatService.sendMessageStream).not.toHaveBeenCalled();
  });

  it('should disable input while sending message', () => {
    store = configureStore({
      reducer: {
        chat: chatReducer,
      },
      preloadedState: {
        chat: {
          sessions: [mockSession],
          currentSession: mockSession,
          messages: { session1: mockMessages },
          isLoading: false,
          isLoadingMessages: false,
          isSending: true,
          error: null,
          streamingMessage: null,
          totalSessions: 1,
        },
      },
    });

    renderComponent();

    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByTestId('SendIcon').closest('button');

    expect(input).toBeDisabled();
    expect(sendButton).toBeDisabled();
  });

  it('should show streaming message', () => {
    store = configureStore({
      reducer: {
        chat: chatReducer,
      },
      preloadedState: {
        chat: {
          sessions: [mockSession],
          currentSession: mockSession,
          messages: { session1: mockMessages },
          isLoading: false,
          isLoadingMessages: false,
          isSending: false,
          error: null,
          streamingMessage: 'This is a streaming response...',
          totalSessions: 1,
        },
      },
    });

    renderComponent();

    expect(screen.getByText('This is a streaming response...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('should handle streaming error', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    (chatService.sendMessageStream as any).mockImplementation(
      async (sessionId, content, onMessage, onComplete, onError) => {
        onError(new Error('Network error'));
      }
    );

    renderComponent();

    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByTestId('SendIcon').closest('button');

    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton!);

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalledWith('Stream error:', expect.any(Error));
    });
    
    consoleSpy.mockRestore();
  });

  it('should show context menu', () => {
    renderComponent();

    const moreButton = screen.getByTestId('MoreVertIcon').closest('button');
    fireEvent.click(moreButton!);

    expect(screen.getByText('Clear History')).toBeInTheDocument();
    expect(screen.getByText('Export Chat')).toBeInTheDocument();
  });

  it('should display correct context icon', () => {
    renderComponent();

    // Document icon should be present for document context
    expect(screen.getByTestId('DescriptionIcon')).toBeInTheDocument();
  });

  it('should not send empty messages', () => {
    renderComponent();

    const sendButton = screen.getByTestId('SendIcon').closest('button');
    fireEvent.click(sendButton!);

    expect(chatService.sendMessageStream).not.toHaveBeenCalled();
  });

  it('should trim whitespace from messages', async () => {
    renderComponent();

    const input = screen.getByPlaceholderText('Type your message...');
    fireEvent.change(input, { target: { value: '  Test message  ' } });

    const sendButton = screen.getByTestId('SendIcon').closest('button');
    fireEvent.click(sendButton!);

    await waitFor(() => {
      expect(chatService.sendMessageStream).toHaveBeenCalledWith(
        'session1',
        'Test message',
        expect.any(Function),
        expect.any(Function),
        expect.any(Function)
      );
    });
  });
});