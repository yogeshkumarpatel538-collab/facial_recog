import { useCallback, useEffect, useRef, useState } from 'react';
import { storage, getWsUrl } from '../utils/storage';

export function useLiveCounts(enabled = true) {
  const [liveCounts, setLiveCounts] = useState({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const reconnectDelay = useRef(1000);

  const connect = useCallback(() => {
    const token = storage.getAccessToken();
    if (!enabled || !token) return;

    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(getWsUrl(token));
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      reconnectDelay.current = 1000;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.camera_id != null) {
          setLiveCounts((prev) => ({
            ...prev,
            [data.camera_id]: {
              total_in: data.total_in,
              total_out: data.total_out,
            },
          }));
        }
      } catch {
        /* ignore malformed messages */
      }
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      if (enabled && storage.getAccessToken()) {
        reconnectTimer.current = setTimeout(() => {
          reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000);
          connect();
        }, reconnectDelay.current);
      }
    };

    ws.onerror = () => ws.close();
  }, [enabled]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send('ping');
    }
  }, []);

  return { liveCounts, connected, sendPing };
}
