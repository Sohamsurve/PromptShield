"use client";

import { create } from "zustand";
import { wsUrl } from "@/lib/api";

type Status = "connecting" | "open" | "closed";

interface WsState {
  status: Status;
  events: unknown[];
  connect: () => void;
}

export const useWsStore = create<WsState>((set, get) => ({
  status: "closed",
  events: [],
  connect: () => {
    if (typeof window === "undefined") return;
    if (get().status === "open" || get().status === "connecting") return;
    set({ status: "connecting" });
    try {
      const ws = new WebSocket(wsUrl("/ws/stream"));
      ws.onopen = () => set({ status: "open" });
      ws.onclose = () => set({ status: "closed" });
      ws.onerror = () => set({ status: "closed" });
      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          set((s) => ({ events: [data, ...s.events].slice(0, 5000) }));
        } catch {
          /* ignore malformed */
        }
      };
    } catch {
      set({ status: "closed" });
    }
  },
}));
