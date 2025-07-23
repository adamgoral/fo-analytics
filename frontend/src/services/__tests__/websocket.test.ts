/**
 * Tests for WebSocket service
 */

import { websocketService, WebSocketMessage } from '../websocket';
import { getAuthToken } from '../auth';

// Mock the auth module
jest.mock('../auth', () => ({
  getAuthToken: jest.fn()
}));

// Mock WebSocket
class MockWebSocket {
  readyState: number;
  url: string;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  
  constructor(url: string) {
    this.url = url;
    this.readyState = WebSocket.CONNECTING;
  }
  
  send = jest.fn();
  close = jest.fn();
  
  // Helper methods for testing
  triggerOpen() {
    this.readyState = WebSocket.OPEN;
    if (this.onopen) {
      this.onopen(new Event('open'));
    }
  }
  
  triggerClose(code = 1000, reason = 'Normal closure') {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      const event = new CloseEvent('close', { code, reason });
      this.onclose(event);
    }
  }
  
  triggerError() {
    if (this.onerror) {
      this.onerror(new Event('error'));
    }
  }
  
  triggerMessage(data: any) {
    if (this.onmessage) {
      const event = new MessageEvent('message', { data: JSON.stringify(data) });
      this.onmessage(event);
    }
  }
}

// Replace global WebSocket
(global as any).WebSocket = MockWebSocket;

describe('WebSocketService', () => {
  let mockGetAuthToken: jest.MockedFunction<typeof getAuthToken>;
  let mockWebSocket: MockWebSocket;
  
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    mockGetAuthToken = getAuthToken as jest.MockedFunction<typeof getAuthToken>;
    
    // Capture WebSocket instance when created
    const originalWebSocket = (global as any).WebSocket;
    (global as any).WebSocket = jest.fn((url: string) => {
      mockWebSocket = new MockWebSocket(url);
      return mockWebSocket;
    });
    
    // Reset service state
    websocketService.disconnect();
  });
  
  afterEach(() => {
    jest.useRealTimers();
    websocketService.disconnect();
  });
  
  describe('connect', () => {
    it('should connect with auth token', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      
      await websocketService.connect();
      
      expect(mockGetAuthToken).toHaveBeenCalled();
      expect(mockWebSocket).toBeDefined();
      expect(mockWebSocket.url).toContain('token=test-token');
    });
    
    it('should not connect without auth token', async () => {
      mockGetAuthToken.mockResolvedValue(null);
      
      await websocketService.connect();
      
      expect(mockWebSocket).toBeUndefined();
    });
    
    it('should not reconnect if already connected', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      
      await websocketService.connect();
      const firstWebSocket = mockWebSocket;
      mockWebSocket.triggerOpen();
      
      await websocketService.connect();
      
      expect(mockWebSocket).toBe(firstWebSocket);
      expect(mockGetAuthToken).toHaveBeenCalledTimes(1);
    });
  });
  
  describe('disconnect', () => {
    it('should close WebSocket connection', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      websocketService.disconnect();
      
      expect(mockWebSocket.close).toHaveBeenCalledWith(1000, 'Client disconnect');
    });
    
    it('should clear timers on disconnect', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      websocketService.disconnect();
      
      // Advance timers - should not trigger any reconnects
      jest.advanceTimersByTime(60000);
      
      expect(mockGetAuthToken).toHaveBeenCalledTimes(1);
    });
  });
  
  describe('isConnected', () => {
    it('should return false when not connected', () => {
      expect(websocketService.isConnected()).toBe(false);
    });
    
    it('should return true when connected', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      expect(websocketService.isConnected()).toBe(true);
    });
    
    it('should return false after disconnect', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      websocketService.disconnect();
      
      expect(websocketService.isConnected()).toBe(false);
    });
  });
  
  describe('subscribe', () => {
    it('should receive messages of subscribed type', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      const handler = jest.fn();
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      websocketService.subscribe('test.message', handler);
      
      const message: WebSocketMessage = {
        type: 'test.message',
        timestamp: new Date().toISOString(),
        data: { value: 123 }
      };
      
      mockWebSocket.triggerMessage(message);
      
      expect(handler).toHaveBeenCalledWith(message);
    });
    
    it('should not receive messages of other types', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      const handler = jest.fn();
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      websocketService.subscribe('test.message', handler);
      
      const message: WebSocketMessage = {
        type: 'other.message',
        timestamp: new Date().toISOString(),
        data: { value: 456 }
      };
      
      mockWebSocket.triggerMessage(message);
      
      expect(handler).not.toHaveBeenCalled();
    });
    
    it('should support wildcard subscription', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      const handler = jest.fn();
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      websocketService.subscribe('*', handler);
      
      const message1: WebSocketMessage = {
        type: 'test.message',
        timestamp: new Date().toISOString(),
        data: { value: 123 }
      };
      
      const message2: WebSocketMessage = {
        type: 'other.message',
        timestamp: new Date().toISOString(),
        data: { value: 456 }
      };
      
      mockWebSocket.triggerMessage(message1);
      mockWebSocket.triggerMessage(message2);
      
      expect(handler).toHaveBeenCalledTimes(2);
      expect(handler).toHaveBeenCalledWith(message1);
      expect(handler).toHaveBeenCalledWith(message2);
    });
    
    it('should return unsubscribe function', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      const handler = jest.fn();
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      const unsubscribe = websocketService.subscribe('test.message', handler);
      
      const message: WebSocketMessage = {
        type: 'test.message',
        timestamp: new Date().toISOString(),
        data: { value: 123 }
      };
      
      mockWebSocket.triggerMessage(message);
      expect(handler).toHaveBeenCalledTimes(1);
      
      unsubscribe();
      
      mockWebSocket.triggerMessage(message);
      expect(handler).toHaveBeenCalledTimes(1);
    });
  });
  
  describe('send', () => {
    it('should send message when connected', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      const message = { type: 'test', data: { value: 123 } };
      websocketService.send(message);
      
      expect(mockWebSocket.send).toHaveBeenCalledWith(JSON.stringify(message));
    });
    
    it('should not send message when not connected', () => {
      const message = { type: 'test', data: { value: 123 } };
      
      websocketService.send(message);
      
      expect(mockWebSocket).toBeUndefined();
    });
  });
  
  describe('reconnection', () => {
    it('should attempt to reconnect on connection close', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      
      await websocketService.connect();
      const firstWebSocket = mockWebSocket;
      mockWebSocket.triggerOpen();
      
      // Trigger close with non-normal code
      mockWebSocket.triggerClose(1006, 'Abnormal closure');
      
      // Advance timer to trigger reconnect
      jest.advanceTimersByTime(5000);
      
      // Should create new connection
      await Promise.resolve(); // Let async operations complete
      
      expect(mockGetAuthToken).toHaveBeenCalledTimes(2);
    });
    
    it('should not reconnect on normal close', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      // Trigger normal close
      mockWebSocket.triggerClose(1000, 'Normal closure');
      
      // Advance timer
      jest.advanceTimersByTime(10000);
      
      // Should not reconnect
      expect(mockGetAuthToken).toHaveBeenCalledTimes(1);
    });
    
    it('should use exponential backoff for reconnection', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      
      // Mock WebSocket to always fail
      let attemptCount = 0;
      (global as any).WebSocket = jest.fn(() => {
        attemptCount++;
        const ws = new MockWebSocket('test-url');
        setTimeout(() => ws.triggerClose(1006, 'Failed'), 10);
        return ws;
      });
      
      await websocketService.connect();
      
      // First reconnect after 5 seconds
      jest.advanceTimersByTime(5000);
      await Promise.resolve();
      expect(attemptCount).toBe(2);
      
      // Second reconnect after 10 seconds (exponential backoff)
      jest.advanceTimersByTime(10000);
      await Promise.resolve();
      expect(attemptCount).toBe(3);
    });
    
    it('should stop reconnecting after max attempts', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      const handler = jest.fn();
      
      // Mock WebSocket to always fail
      (global as any).WebSocket = jest.fn(() => {
        const ws = new MockWebSocket('test-url');
        setTimeout(() => ws.triggerClose(1006, 'Failed'), 10);
        return ws;
      });
      
      websocketService.subscribe('connection.failed', handler);
      
      await websocketService.connect();
      
      // Advance through all reconnection attempts
      for (let i = 0; i < 10; i++) {
        jest.advanceTimersByTime(30000);
        await Promise.resolve();
      }
      
      // Should receive connection failed message
      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'connection.failed',
          data: expect.objectContaining({
            reason: expect.stringContaining('Max reconnection attempts')
          })
        })
      );
    });
  });
  
  describe('ping/pong', () => {
    it('should send ping messages periodically', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      // Advance timer to trigger ping
      jest.advanceTimersByTime(30000);
      
      expect(mockWebSocket.send).toHaveBeenCalledWith(
        expect.stringContaining('"type":"ping"')
      );
    });
    
    it('should handle pong messages', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      const handler = jest.fn();
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      // Subscribe to all messages
      websocketService.subscribe('*', handler);
      
      const pongMessage: WebSocketMessage = {
        type: 'pong',
        timestamp: new Date().toISOString(),
        data: {}
      };
      
      mockWebSocket.triggerMessage(pongMessage);
      
      // Pong messages should not be passed to handlers
      expect(handler).not.toHaveBeenCalled();
    });
  });
  
  describe('connection events', () => {
    it('should notify on connection open', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      const handler = jest.fn();
      
      websocketService.subscribe('connection.open', handler);
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'connection.open',
          timestamp: expect.any(String),
          data: {}
        })
      );
    });
    
    it('should notify on connection close', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      const handler = jest.fn();
      
      websocketService.subscribe('connection.closed', handler);
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      mockWebSocket.triggerClose(1000, 'Test close');
      
      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'connection.closed',
          data: { code: 1000, reason: 'Test close' }
        })
      );
    });
    
    it('should notify on connection error', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      const handler = jest.fn();
      
      websocketService.subscribe('connection.error', handler);
      
      await websocketService.connect();
      mockWebSocket.triggerError();
      
      expect(handler).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'connection.error',
          data: { error: 'WebSocket error occurred' }
        })
      );
    });
  });
  
  describe('visibility change handling', () => {
    it('should reconnect when tab becomes visible', async () => {
      mockGetAuthToken.mockResolvedValue('test-token');
      
      // Simulate tab becoming hidden
      Object.defineProperty(document, 'visibilityState', {
        configurable: true,
        get: () => 'hidden'
      });
      
      await websocketService.connect();
      mockWebSocket.triggerOpen();
      
      // Close connection
      websocketService.disconnect();
      
      // Simulate tab becoming visible
      Object.defineProperty(document, 'visibilityState', {
        configurable: true,
        get: () => 'visible'
      });
      
      document.dispatchEvent(new Event('visibilitychange'));
      
      // Should attempt to reconnect
      await Promise.resolve();
      expect(mockGetAuthToken).toHaveBeenCalledTimes(2);
    });
  });
});