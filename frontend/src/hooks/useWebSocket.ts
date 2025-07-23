/**
 * React hook for WebSocket subscriptions
 */

import { useEffect, useRef } from 'react';
import { websocketService, WebSocketMessage, MessageHandler } from '../services/websocket';
import { useAuth } from './useAuth';

export interface UseWebSocketOptions {
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: any) => void;
}

/**
 * Hook to subscribe to WebSocket messages
 * @param messageType - The message type to subscribe to (use '*' for all messages)
 * @param handler - The message handler function
 * @param options - Additional options
 */
export function useWebSocket(
  messageType: string,
  handler: MessageHandler,
  options: UseWebSocketOptions = {}
): void {
  const { isAuthenticated } = useAuth();
  const handlerRef = useRef(handler);
  const optionsRef = useRef(options);

  // Update refs when they change
  handlerRef.current = handler;
  optionsRef.current = options;

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    // Connect to WebSocket if not already connected
    websocketService.connect();

    // Subscribe to the message type
    const unsubscribe = websocketService.subscribe(messageType, handlerRef.current);

    // Subscribe to connection events if callbacks provided
    const unsubscribers: (() => void)[] = [unsubscribe];

    if (optionsRef.current.onConnect) {
      const unsubConnect = websocketService.subscribe('connection.open', () => {
        optionsRef.current.onConnect?.();
      });
      unsubscribers.push(unsubConnect);
    }

    if (optionsRef.current.onDisconnect) {
      const unsubDisconnect = websocketService.subscribe('connection.closed', () => {
        optionsRef.current.onDisconnect?.();
      });
      unsubscribers.push(unsubDisconnect);
    }

    if (optionsRef.current.onError) {
      const unsubError = websocketService.subscribe('connection.error', (msg) => {
        optionsRef.current.onError?.(msg.data);
      });
      unsubscribers.push(unsubError);
    }

    // Cleanup
    return () => {
      unsubscribers.forEach(unsub => unsub());
    };
  }, [messageType, isAuthenticated]);
}

/**
 * Hook to get WebSocket connection status
 */
export function useWebSocketStatus() {
  const { isAuthenticated } = useAuth();
  
  return {
    isConnected: isAuthenticated && websocketService.isConnected(),
    connect: () => websocketService.connect(),
    disconnect: () => websocketService.disconnect()
  };
}