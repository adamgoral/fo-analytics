import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { BrowserRouter } from 'react-router-dom';
import ChatSidebar from '../ChatSidebar';
import chatReducer from '../../../store/slices/chatSlice';
import { chatService } from '../../../services/chat';

// Mock the chat service
vi.mock('../../../services/chat', () => ({
  chatService: {
    createSession: vi.fn(),
    deleteSession: vi.fn(),
  },
}));

// Create mock dispatch function
const mockDispatch = vi.fn((action: any) => {
  if (action.type?.includes('fulfilled')) {
    return Promise.resolve(action);
  }
  return Promise.resolve({ type: action.type });
});

// Mock the useAppDispatch and useAppSelector hooks
vi.mock('../../../store', () => ({
  useAppDispatch: () => mockDispatch,
  useAppSelector: (selector: any) => selector({
    chat: {
      sessions: mockSessions,
      currentSession: mockCurrentSession,
      isLoading: false,
    },
  }),
}));

const mockSessions = [
  {
    id: '1',
    name: 'General Chat',
    context_type: 'general',
    updated_at: '2024-01-01T10:00:00Z',
  },
  {
    id: '2',
    name: 'Document Analysis',
    context_type: 'document',
    updated_at: '2024-01-01T11:00:00Z',
  },
];

let mockCurrentSession: any = null;

describe('ChatSidebar', () => {
  let store: any;
  const mockOnSessionSelect = vi.fn();

  beforeEach(() => {
    store = configureStore({
      reducer: {
        chat: chatReducer,
      },
    });
    mockCurrentSession = null;
    vi.clearAllMocks();
  });

  const renderComponent = () => {
    return render(
      <Provider store={store}>
        <BrowserRouter>
          <ChatSidebar onSessionSelect={mockOnSessionSelect} />
        </BrowserRouter>
      </Provider>
    );
  };

  it('should render sidebar with header', () => {
    renderComponent();

    expect(screen.getByText('Chat Sessions')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /new chat/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Search sessions...')).toBeInTheDocument();
  });

  it('should display chat sessions', () => {
    renderComponent();

    expect(screen.getByText('General Chat')).toBeInTheDocument();
    expect(screen.getByText('Document Analysis')).toBeInTheDocument();
    expect(screen.getByText('General')).toBeInTheDocument();
    expect(screen.getByText('Document')).toBeInTheDocument();
  });

  it('should filter sessions based on search', () => {
    renderComponent();

    const searchInput = screen.getByPlaceholderText('Search sessions...');
    fireEvent.change(searchInput, { target: { value: 'Document' } });

    expect(screen.getByText('Document Analysis')).toBeInTheDocument();
    expect(screen.queryByText('General Chat')).not.toBeInTheDocument();
  });

  it('should open new chat dialog when clicking new chat button', () => {
    renderComponent();

    const newChatButton = screen.getByRole('button', { name: /new chat/i });
    fireEvent.click(newChatButton);

    expect(screen.getByText('Create New Chat Session')).toBeInTheDocument();
    expect(screen.getByLabelText('Session Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Context Type')).toBeInTheDocument();
  });

  it('should create a new chat session', async () => {
    const newSession = {
      id: '3',
      name: 'New Chat',
      context_type: 'strategy',
      user_id: 'user1',
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
    };

    mockDispatch.mockImplementationOnce((action: any) => {
      if (action.type === 'chat/createSession/fulfilled') {
        return Promise.resolve({ type: action.type, payload: newSession });
      }
      return Promise.resolve(action);
    });

    renderComponent();

    // Open dialog
    fireEvent.click(screen.getByRole('button', { name: /new chat/i }));

    // Fill form
    fireEvent.change(screen.getByLabelText('Session Name'), {
      target: { value: 'New Chat' },
    });

    // Click create
    const createButton = screen.getByRole('button', { name: 'Create' });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(mockDispatch).toHaveBeenCalled();
    });
  });

  it('should highlight selected session', () => {
    mockCurrentSession = { id: '1', name: 'General Chat' };
    renderComponent();

    const sessions = screen.getAllByRole('button');
    const generalChatButton = sessions.find(btn => 
      btn.textContent?.includes('General Chat')
    );

    expect(generalChatButton).toHaveClass('Mui-selected');
  });

  it('should handle session selection', () => {
    renderComponent();

    const sessionButton = screen.getByText('Document Analysis').closest('button');
    if (sessionButton) {
      fireEvent.click(sessionButton);
    }

    expect(mockOnSessionSelect).toHaveBeenCalledWith('2');
  });

  it('should show context menu on more button click', () => {
    renderComponent();

    const moreButtons = screen.getAllByTestId('MoreVertIcon');
    fireEvent.click(moreButtons[0]);

    expect(screen.getByText('Rename')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();
  });

  it('should handle session deletion', async () => {
    mockDispatch.mockImplementationOnce((action: any) => {
      if (action.type === 'chat/deleteSession/fulfilled') {
        return Promise.resolve({ type: action.type, payload: '1' });
      }
      return Promise.resolve(action);
    });

    renderComponent();

    // Click more button for first session
    const moreButtons = screen.getAllByTestId('MoreVertIcon');
    fireEvent.click(moreButtons[0]);

    // Click delete
    fireEvent.click(screen.getByText('Delete'));

    await waitFor(() => {
      expect(mockDispatch).toHaveBeenCalled();
    });
  });

  it('should show loading state when loading', () => {
    // Re-mock with loading state
    vi.unmock('../../../store');
    vi.mock('../../../store', () => ({
      useAppDispatch: () => vi.fn(),
      useAppSelector: () => ({
        sessions: [],
        currentSession: null,
        isLoading: true,
      }),
    }));

    renderComponent();

    // Check for skeleton elements - Material UI Skeleton doesn't use data-testid by default
    const loadingElements = document.querySelectorAll('.MuiSkeleton-root');
    expect(loadingElements.length).toBeGreaterThan(0);
  });

  it('should disable create button when session name is empty', () => {
    renderComponent();

    fireEvent.click(screen.getByRole('button', { name: /new chat/i }));

    const createButton = screen.getByRole('button', { name: 'Create' });
    expect(createButton).toBeDisabled();

    // Type a name
    fireEvent.change(screen.getByLabelText('Session Name'), {
      target: { value: 'Test' },
    });

    expect(createButton).not.toBeDisabled();
  });
});