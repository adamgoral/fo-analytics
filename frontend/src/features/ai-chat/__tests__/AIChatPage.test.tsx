import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, act, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { BrowserRouter } from 'react-router-dom';
import AIChatPage from '../AIChatPage';
import chatReducer from '../../../store/slices/chatSlice';

// Mock child components
vi.mock('../ChatSidebar', () => ({
  default: ({ onSessionSelect }: any) => {
    // Simulate the component's behavior when it mounts
    React.useEffect(() => {
      // Simulate fetching sessions on mount
    }, []);
    
    return (
      <div data-testid="chat-sidebar">
        <button onClick={() => onSessionSelect('session1')}>Select Session</button>
      </div>
    );
  },
}));

vi.mock('../ChatInterface', () => ({
  default: ({ sessionId }: any) => (
    <div data-testid="chat-interface">Chat Interface for {sessionId}</div>
  ),
}));

describe('AIChatPage', () => {
  let store: any;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        chat: chatReducer,
      },
    });
    vi.clearAllMocks();
  });

  const renderComponent = (preloadedState?: any) => {
    if (preloadedState) {
      store = configureStore({
        reducer: {
          chat: chatReducer,
        },
        preloadedState,
      });
    }

    return render(
      <Provider store={store}>
        <BrowserRouter>
          <AIChatPage />
        </BrowserRouter>
      </Provider>
    );
  };

  it('should render sidebar and welcome message by default', () => {
    renderComponent();

    expect(screen.getByTestId('chat-sidebar')).toBeInTheDocument();
    expect(screen.getByText('Welcome to AI Chat Assistant')).toBeInTheDocument();
    expect(screen.getByText(/Select a chat session from the sidebar/)).toBeInTheDocument();
  });

  it('should render chat interface when session is selected', async () => {
    const { rerender } = renderComponent();

    // Initially no session selected
    expect(screen.queryByTestId('chat-interface')).not.toBeInTheDocument();

    // Now render with a selected session
    store = configureStore({
      reducer: {
        chat: chatReducer,
      },
      preloadedState: {
        chat: {
          sessions: [{ id: 'session1', name: 'Test Session' }],
          currentSession: { id: 'session1', name: 'Test Session' },
          messages: {},
          isLoading: false,
          isLoadingMessages: false,
          isSending: false,
          error: null,
          streamingMessage: null,
          totalSessions: 1,
        },
      },
    });

    await act(async () => {
      rerender(
        <Provider store={store}>
          <BrowserRouter>
            <AIChatPage />
          </BrowserRouter>
        </Provider>
      );
    });

    // Simulate selecting a session
    const button = screen.getByText('Select Session');
    
    await act(async () => {
      button.click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
    });
  });

  it('should display welcome content with proper text', () => {
    renderComponent();

    expect(screen.getByText('Welcome to AI Chat Assistant')).toBeInTheDocument();
    expect(
      screen.getByText(/Select a chat session from the sidebar or create a new one to start chatting/)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/The AI assistant has access to your uploaded documents/)
    ).toBeInTheDocument();
  });

  it('should have proper layout structure', () => {
    renderComponent();

    const container = screen.getByTestId('chat-sidebar').parentElement?.parentElement;
    expect(container).toHaveStyle({ display: 'flex' });
  });

  it('should handle session selection', () => {
    renderComponent({
      chat: {
        sessions: [{ id: 'session1', name: 'Test Session' }],
        currentSession: { id: 'session1', name: 'Test Session' },
        messages: {},
        isLoading: false,
        isLoadingMessages: false,
        isSending: false,
        error: null,
        streamingMessage: null,
        totalSessions: 1,
      },
    });

    // Select session
    const button = screen.getByText('Select Session');
    button.click();

    // Should render chat interface after selection
    expect(screen.getByTestId('chat-interface')).toBeInTheDocument();
  });

  it('should show chat interface only when both sessionId and currentSession exist', () => {
    // Test with sessionId but no currentSession
    renderComponent({
      chat: {
        sessions: [],
        currentSession: null,
        messages: {},
        isLoading: false,
        isLoadingMessages: false,
        isSending: false,
        error: null,
        streamingMessage: null,
        totalSessions: 0,
      },
    });

    expect(screen.queryByTestId('chat-interface')).not.toBeInTheDocument();
    expect(screen.getByText('Welcome to AI Chat Assistant')).toBeInTheDocument();
  });
});