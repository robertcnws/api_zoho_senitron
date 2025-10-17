// use-websocket.js
import { useRef, useEffect, useCallback } from 'react';

const __wsStarted = new Set();

export function useWebsocket(url, onMessage) {
  const wsRef = useRef(null);
  const openedRef = useRef(false);      
  const connectingRef = useRef(false);  

  const onMsg = useCallback((evt) => {
    try { onMessage?.(JSON.parse(evt.data)); } catch { /* ignore */ }
  }, [onMessage]);

  useEffect(() => {
    if (wsRef.current || connectingRef.current) return () => {}; 
    connectingRef.current = true;

    if (import.meta.env.DEV && !__wsStarted.has(url)) {
      __wsStarted.add(url);
      return () => {};
    }

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => { openedRef.current = true; connectingRef.current = false; console.log('WS open', url); };
    ws.onmessage = onMsg;
    ws.onerror = (e) => { if (openedRef.current) console.error('WS error', e); };
    ws.onclose  = (e) => { if (openedRef.current) console.warn('WS close', e.code, e.reason || ''); };

    const ping = setInterval(() => { 
        if (ws.readyState === WebSocket.OPEN) try { ws.send('ping'); } catch { console.warn('WS ping error'); } 
    }, 30000);

    return () => {
      clearInterval(ping);
      try { ws.close(1000, 'component unmount'); } catch { console.warn('WS close error'); }
      wsRef.current = null;
      openedRef.current = false;
      connectingRef.current = false;
    };
  }, [url, onMsg]);

  return wsRef;
}
