/**
 * WebSocket service for real-time updates
 */

import { getAuthToken } from './auth';

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  data: any;
}

export type MessageHandler = (message: WebSocketMessage) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectInterval: number = 5000;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectTimer: NodeJS.Timeout | null = null;
  private pingInterval: NodeJS.Timeout | null = null;
  private shouldReconnect: boolean = true;

  constructor() {
    // Set up visibility change listener to handle tab switching
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && this.shouldReconnect && !this.isConnected()) {
        this.connect();
      }
    });
  }

  /**
   * Connect to the WebSocket server
   */
  async connect(): Promise<void> {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    const token = await getAuthToken();
    if (!token) {
      console.error('No auth token available for WebSocket connection');
      return;
    }

    const wsUrl = this.getWebSocketUrl(token);
    
    try {
      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    this.shouldReconnect = false;
    this.clearTimers();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  /**
   * Check if WebSocket is connected
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Subscribe to a specific message type
   */
  subscribe(messageType: string, handler: MessageHandler): () => void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, new Set());
    }
    
    this.messageHandlers.get(messageType)!.add(handler);
    
    // Return unsubscribe function
    return () => {
      const handlers = this.messageHandlers.get(messageType);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.messageHandlers.delete(messageType);
        }
      }
    };
  }

  /**
   * Send a message to the server
   */
  send(message: any): void {
    if (!this.isConnected()) {
      console.warn('WebSocket not connected, cannot send message');
      return;
    }

    try {
      this.ws!.send(JSON.stringify(message));
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
    }
  }

  private getWebSocketUrl(token: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = import.meta.env.VITE_API_URL?.replace(/^https?:\/\//, '') || window.location.host;
    return `${protocol}//${host}/api/v1/ws?token=${encodeURIComponent(token)}`;
  }

  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.startPingInterval();
      this.notifyHandlers({ type: 'connection.open', timestamp: new Date().toISOString(), data: {} });
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.clearTimers();
      this.notifyHandlers({ type: 'connection.closed', timestamp: new Date().toISOString(), data: { code: event.code, reason: event.reason } });
      
      if (this.shouldReconnect && event.code !== 1000) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.notifyHandlers({ type: 'connection.error', timestamp: new Date().toISOString(), data: { error: 'WebSocket error occurred' } });
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as WebSocketMessage;
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
  }

  private handleMessage(message: WebSocketMessage): void {
    // Handle ping/pong
    if (message.type === 'pong') {
      return;
    }

    // Notify all handlers for this message type
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error(`Error in message handler for ${message.type}:`, error);
        }
      });
    }

    // Also notify wildcard handlers
    const wildcardHandlers = this.messageHandlers.get('*');
    if (wildcardHandlers) {
      wildcardHandlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in wildcard message handler:', error);
        }
      });
    }
  }

  private notifyHandlers(message: WebSocketMessage): void {
    this.handleMessage(message);
  }

  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: 'ping', timestamp: new Date().toISOString() });
      }
    }, 30000); // Ping every 30 seconds
  }

  private clearTimers(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private scheduleReconnect(): void {
    if (!this.shouldReconnect || this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.notifyHandlers({ 
        type: 'connection.failed', 
        timestamp: new Date().toISOString(), 
        data: { reason: 'Max reconnection attempts reached' } 
      });
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts} in ${delay}ms`);
    
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, delay);
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();

// Export message types for TypeScript
export interface DocumentUploadStartedMessage extends WebSocketMessage {
  type: 'document.upload.started';
  data: {
    document_id: string;
    filename: string;
  };
}

export interface DocumentUploadCompletedMessage extends WebSocketMessage {
  type: 'document.upload.completed';
  data: {
    document_id: string;
    filename: string;
  };
}

export interface DocumentProcessingStartedMessage extends WebSocketMessage {
  type: 'document.processing.started';
  data: {
    document_id: string;
  };
}

export interface DocumentProcessingProgressMessage extends WebSocketMessage {
  type: 'document.processing.progress';
  data: {
    document_id: string;
    progress: number;
    message: string;
  };
}

export interface DocumentProcessingCompletedMessage extends WebSocketMessage {
  type: 'document.processing.completed';
  data: {
    document_id: string;
    strategies_count: number;
  };
}

export interface DocumentProcessingFailedMessage extends WebSocketMessage {
  type: 'document.processing.failed';
  data: {
    document_id: string;
    error: string;
  };
}

export interface StrategyExtractedMessage extends WebSocketMessage {
  type: 'strategy.extracted';
  data: {
    document_id: string;
    strategy_id: string;
    strategy_name: string;
  };
}