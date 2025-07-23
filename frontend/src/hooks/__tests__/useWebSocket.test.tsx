/**
 * Tests for useWebSocket hook
 */

import { renderHook, act } from '@testing-library/react';
import { useWebSocket, useWebSocketStatus } from '../useWebSocket';
import { websocketService } from '../../services/websocket';
import { useAuth } from '../useAuth';

// Mock dependencies
jest.mock('../../services/websocket', () => ({
  websocketService: {
    connect: jest.fn(),
    disconnect: jest.fn(),
    subscribe: jest.fn(),
    isConnected: jest.fn()
  }
}));

jest.mock('../useAuth', () => ({
  useAuth: jest.fn()
}));

describe('useWebSocket', () => {
  const mockConnect = websocketService.connect as jest.MockedFunction<typeof websocketService.connect>;
  const mockSubscribe = websocketService.subscribe as jest.MockedFunction<typeof websocketService.subscribe>;
  const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
  
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: '1', email: 'test@example.com', role: 'analyst' },
      loading: false,
      error: null,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      updatePassword: jest.fn(),
      clearError: jest.fn(),
      refreshUser: jest.fn(),
      isAdmin: false,
      isAnalyst: true,
      isViewer: false,
      canManageUsers: false,
      canUploadDocuments: true,
      canViewStrategies: true
    });
  });
  
  describe('subscription management', () => {
    it('should subscribe to message type when authenticated', () => {
      const handler = jest.fn();
      const unsubscribe = jest.fn();
      mockSubscribe.mockReturnValue(unsubscribe);
      
      renderHook(() => useWebSocket('test.message', handler));
      
      expect(mockConnect).toHaveBeenCalled();
      expect(mockSubscribe).toHaveBeenCalledWith('test.message', handler);
    });
    
    it('should not subscribe when not authenticated', () => {
      mockUseAuth.mockReturnValue({
        ...mockUseAuth(),
        isAuthenticated: false
      });
      
      const handler = jest.fn();
      renderHook(() => useWebSocket('test.message', handler));
      
      expect(mockConnect).not.toHaveBeenCalled();
      expect(mockSubscribe).not.toHaveBeenCalled();
    });
    
    it('should unsubscribe on unmount', () => {
      const handler = jest.fn();
      const unsubscribe = jest.fn();
      mockSubscribe.mockReturnValue(unsubscribe);
      
      const { unmount } = renderHook(() => useWebSocket('test.message', handler));
      
      unmount();
      
      expect(unsubscribe).toHaveBeenCalled();
    });
    
    it('should resubscribe when message type changes', () => {
      const handler = jest.fn();
      const unsubscribe1 = jest.fn();
      const unsubscribe2 = jest.fn();
      
      mockSubscribe
        .mockReturnValueOnce(unsubscribe1)
        .mockReturnValueOnce(unsubscribe2);
      
      const { rerender } = renderHook(
        ({ messageType }) => useWebSocket(messageType, handler),
        { initialProps: { messageType: 'type1' } }
      );
      
      expect(mockSubscribe).toHaveBeenCalledWith('type1', handler);
      
      rerender({ messageType: 'type2' });
      
      expect(unsubscribe1).toHaveBeenCalled();
      expect(mockSubscribe).toHaveBeenCalledWith('type2', handler);
    });
    
    it('should use latest handler without resubscribing', () => {
      let handlerVersion = 1;
      const unsubscribe = jest.fn();
      mockSubscribe.mockReturnValue(unsubscribe);
      
      const { rerender } = renderHook(() => {
        const handler = jest.fn().mockImplementation(() => handlerVersion);
        useWebSocket('test.message', handler);
        return handler;
      });
      
      handlerVersion = 2;
      rerender();
      
      // Should not resubscribe
      expect(mockSubscribe).toHaveBeenCalledTimes(1);
      expect(unsubscribe).not.toHaveBeenCalled();
    });
  });
  
  describe('connection callbacks', () => {
    it('should subscribe to connection events when callbacks provided', () => {
      const handler = jest.fn();
      const onConnect = jest.fn();
      const onDisconnect = jest.fn();
      const onError = jest.fn();
      
      const unsubscribes = [jest.fn(), jest.fn(), jest.fn(), jest.fn()];
      mockSubscribe.mockImplementation(() => unsubscribes[mockSubscribe.mock.calls.length - 1]);
      
      renderHook(() => useWebSocket('test.message', handler, {
        onConnect,
        onDisconnect,
        onError
      }));
      
      expect(mockSubscribe).toHaveBeenCalledTimes(4);
      expect(mockSubscribe).toHaveBeenCalledWith('test.message', handler);
      expect(mockSubscribe).toHaveBeenCalledWith('connection.open', expect.any(Function));
      expect(mockSubscribe).toHaveBeenCalledWith('connection.closed', expect.any(Function));
      expect(mockSubscribe).toHaveBeenCalledWith('connection.error', expect.any(Function));
    });
    
    it('should call onConnect callback', () => {
      const handler = jest.fn();
      const onConnect = jest.fn();
      
      mockSubscribe.mockImplementation((type, fn) => {
        if (type === 'connection.open') {
          // Simulate connection open
          fn({ type: 'connection.open', timestamp: new Date().toISOString(), data: {} });
        }
        return jest.fn();
      });
      
      renderHook(() => useWebSocket('test.message', handler, { onConnect }));
      
      expect(onConnect).toHaveBeenCalled();
    });
    
    it('should call onDisconnect callback', () => {
      const handler = jest.fn();
      const onDisconnect = jest.fn();
      
      mockSubscribe.mockImplementation((type, fn) => {
        if (type === 'connection.closed') {
          fn({ type: 'connection.closed', timestamp: new Date().toISOString(), data: {} });
        }
        return jest.fn();
      });
      
      renderHook(() => useWebSocket('test.message', handler, { onDisconnect }));
      
      expect(onDisconnect).toHaveBeenCalled();
    });
    
    it('should call onError callback with error data', () => {
      const handler = jest.fn();
      const onError = jest.fn();
      
      mockSubscribe.mockImplementation((type, fn) => {
        if (type === 'connection.error') {
          fn({ 
            type: 'connection.error', 
            timestamp: new Date().toISOString(), 
            data: { error: 'Connection failed' } 
          });
        }
        return jest.fn();
      });
      
      renderHook(() => useWebSocket('test.message', handler, { onError }));
      
      expect(onError).toHaveBeenCalledWith({ error: 'Connection failed' });
    });
  });
  
  describe('authentication changes', () => {
    it('should connect when becoming authenticated', () => {
      const handler = jest.fn();
      const unsubscribe = jest.fn();
      mockSubscribe.mockReturnValue(unsubscribe);
      
      mockUseAuth.mockReturnValue({
        ...mockUseAuth(),
        isAuthenticated: false
      });
      
      const { rerender } = renderHook(() => {
        useWebSocket('test.message', handler);
        return useAuth();
      });
      
      expect(mockConnect).not.toHaveBeenCalled();
      
      // Become authenticated
      mockUseAuth.mockReturnValue({
        ...mockUseAuth(),
        isAuthenticated: true
      });
      
      rerender();
      
      expect(mockConnect).toHaveBeenCalled();
      expect(mockSubscribe).toHaveBeenCalled();
    });
    
    it('should cleanup when becoming unauthenticated', () => {
      const handler = jest.fn();
      const unsubscribe = jest.fn();
      mockSubscribe.mockReturnValue(unsubscribe);
      
      const { rerender } = renderHook(() => {
        useWebSocket('test.message', handler);
        return useAuth();
      });
      
      expect(mockSubscribe).toHaveBeenCalled();
      
      // Become unauthenticated
      mockUseAuth.mockReturnValue({
        ...mockUseAuth(),
        isAuthenticated: false
      });
      
      rerender();
      
      expect(unsubscribe).toHaveBeenCalled();
    });
  });
});

describe('useWebSocketStatus', () => {
  const mockConnect = websocketService.connect as jest.MockedFunction<typeof websocketService.connect>;
  const mockDisconnect = websocketService.disconnect as jest.MockedFunction<typeof websocketService.disconnect>;
  const mockIsConnected = websocketService.isConnected as jest.MockedFunction<typeof websocketService.isConnected>;
  const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
  
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      user: { id: '1', email: 'test@example.com', role: 'analyst' },
      loading: false,
      error: null,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      updatePassword: jest.fn(),
      clearError: jest.fn(),
      refreshUser: jest.fn(),
      isAdmin: false,
      isAnalyst: true,
      isViewer: false,
      canManageUsers: false,
      canUploadDocuments: true,
      canViewStrategies: true
    });
  });
  
  it('should return connection status', () => {
    mockIsConnected.mockReturnValue(true);
    
    const { result } = renderHook(() => useWebSocketStatus());
    
    expect(result.current.isConnected).toBe(true);
  });
  
  it('should return false when not authenticated', () => {
    mockUseAuth.mockReturnValue({
      ...mockUseAuth(),
      isAuthenticated: false
    });
    mockIsConnected.mockReturnValue(true);
    
    const { result } = renderHook(() => useWebSocketStatus());
    
    expect(result.current.isConnected).toBe(false);
  });
  
  it('should provide connect function', () => {
    const { result } = renderHook(() => useWebSocketStatus());
    
    act(() => {
      result.current.connect();
    });
    
    expect(mockConnect).toHaveBeenCalled();
  });
  
  it('should provide disconnect function', () => {
    const { result } = renderHook(() => useWebSocketStatus());
    
    act(() => {
      result.current.disconnect();
    });
    
    expect(mockDisconnect).toHaveBeenCalled();
  });
});