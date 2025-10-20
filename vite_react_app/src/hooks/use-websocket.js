// use-websocket.js
import { useEffect, useRef } from 'react';

// Singleton por URL: { ws, listeners:Set<fn>, refCount:number, opened:boolean }
const socketPool = new Map();

/**
 * Hook WebSocket sin conexiones duplicadas:
 * - 1 socket por URL (compartido), con refCount
 * - No re-crea por cambios de onMessage (usa ref)
 * - Broadcast del mensaje a los listeners registrados por hook
 */
export function useWebsocket(url, onMessage) {
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage; // siempre apunta al handler más reciente

  useEffect(() => {
    if (!url) return;

    // crea u obtiene el socket compartido
    let entry = socketPool.get(url);
    if (!entry) {
      const ws = new WebSocket(url);
      entry = {
        ws,
        listeners: new Set(),
        refCount: 0,
        opened: false,
      };

      ws.onopen = () => {
        entry.opened = true;
        // console.log('[WS open]', url);
      };

      ws.onmessage = (evt) => {
        let data = evt.data;
        try {
          // intenta parsear JSON solo una vez
          data = JSON.parse(evt.data);
        } catch (_) { /* deja data como string */ }
        // notifica a todos los listeners actuales
        entry.listeners.forEach((fn) => {
          try { fn(data); } catch { /* noop */ }
        });
      };

      ws.onerror = (e) => {
        // Evita ruido antes de abrir (p.ej. policy codes en handshake)
        if (entry.opened) console.error('[WS error]', e);
      };

      ws.onclose = (e) => {
        if (entry.opened && e.code !== 1000) {
          console.warn('[WS close]', e.code, e.reason || '');
        }
        entry.opened = false;
        // cuando se cierra (por server u onCleanup), limpia el pool
        socketPool.delete(url);
      };

      socketPool.set(url, entry);
    }

    // registra el listener del componente
    const listener = (payload) => {
      try { onMessageRef.current?.(payload); } catch { /* noop */ }
    };
    entry.listeners.add(listener);
    entry.refCount += 1;

    // cleanup del hook
    // eslint-disable-next-line consistent-return
    return () => {
      // des-registra listener y baja refCount
      if (!socketPool.has(url)) return;
      const cur = socketPool.get(url);
      cur.listeners.delete(listener);
      cur.refCount -= 1;

      // cierra el socket cuando ya no hay consumidores
      if (cur.refCount <= 0) {
        try { cur.ws.close(1000, 'no consumers'); } catch { /* noop */ }
        socketPool.delete(url);
      }
    };
  }, [url]);

  // opcionalmente puedes exponer una API mínima para enviar
  const apiRef = useRef({
    send: (data) => {
      const entry = socketPool.get(url);
      if (!entry || entry.ws.readyState !== WebSocket.OPEN) return false;
      try {
        entry.ws.send(typeof data === 'string' ? data : JSON.stringify(data));
        return true;
      } catch {
        return false;
      }
    },
    get readyState() {
      const entry = socketPool.get(url);
      return entry ? entry.ws.readyState : WebSocket.CLOSED;
    },
  });

  return apiRef.current;
}



// // use-websocket.js
// import { useRef, useEffect, useCallback } from 'react';

// const __wsStarted = new Set();

// export function useWebsocket(url, onMessage) {
//   const wsRef = useRef(null);
//   const openedRef = useRef(false);
//   const connectingRef = useRef(false);

//   const onMsg = useCallback((evt) => {
//     try { onMessage?.(JSON.parse(evt.data)); } catch { /* ignore */ }
//   }, [onMessage]);

//   useEffect(() => {
//     if (wsRef.current || connectingRef.current) return () => { };
//     connectingRef.current = true;

//     if (import.meta.env.DEV && !__wsStarted.has(url)) {
//       __wsStarted.add(url);
//       return () => { };
//     }

//     const ws = new WebSocket(url);
//     wsRef.current = ws;

//     ws.onopen = () => {
//       openedRef.current = true;
//       connectingRef.current = false;
//       // console.log('WS open', url); 
//     };
//     ws.onmessage = onMsg;
//     ws.onerror = (e) => { if (openedRef.current) console.error('WS error', e); };
//     ws.onclose = (e) => {
//       if (openedRef.current)
//         console.warn('WS close', e.code, e.reason || '');
//     };

//     // const ping = setInterval(() => {
//     //   if (ws.readyState === WebSocket.OPEN) try { ws.send('ping'); } catch { console.warn('WS ping error'); }
//     // }, 30000);

//     return () => {
//       // clearInterval(ping);
//       try { ws.close(1000, 'component unmount'); } catch { console.warn('WS close error'); }
//       wsRef.current = null;
//       openedRef.current = false;
//       connectingRef.current = false;
//     };
//   }, [url, onMsg]);

//   return wsRef;
// }
