import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

const INVALIDATION_MAP: Record<string, string[][]> = {
  project: [["projects"], ["stats"], ["activity"]],
  employee: [["employees"], ["stats"], ["activity"]],
  meeting: [["meetings"], ["stats"], ["activity"]],
  user: [["users"], ["activity"]],
};

export function useWebSocket() {
  const qc = useQueryClient();
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retryDelay = useRef(1000);
  const retryTimer = useRef<ReturnType<typeof setTimeout>>();
  const unmounted = useRef(false);

  const connect = useCallback(() => {
    if (unmounted.current) return;
    const token = localStorage.getItem("access_token");
    if (!token) return;

    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${proto}//${window.location.host}/ws?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      retryDelay.current = 1000;
    };

    ws.onmessage = (e) => {
      try {
        const { type } = JSON.parse(e.data) as { type: string };
        const entity = type.split(".")[0];
        const keys = INVALIDATION_MAP[entity] ?? [];
        for (const key of keys) {
          qc.invalidateQueries({ queryKey: key });
        }
      } catch {
        // malformed message — ignore
      }
    };

    ws.onclose = () => {
      if (unmounted.current) return;
      setConnected(false);
      retryTimer.current = setTimeout(() => {
        retryDelay.current = Math.min(retryDelay.current * 2, 30_000);
        connect();
      }, retryDelay.current);
    };

    ws.onerror = () => ws.close();
  }, [qc]);

  useEffect(() => {
    unmounted.current = false;
    connect();
    return () => {
      unmounted.current = true;
      clearTimeout(retryTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected };
}
