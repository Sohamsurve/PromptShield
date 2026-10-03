"use client";

import { useEffect } from "react";
import { useWsStore } from "@/lib/ws-store";

export function ConnectionDot() {
  const status = useWsStore((s) => s.status);
  const connect = useWsStore((s) => s.connect);

  useEffect(() => {
    connect();
  }, [connect]);

  const colour =
    status === "open" ? "bg-allow" : status === "connecting" ? "bg-sanitize" : "bg-block";
  const label = status === "open" ? "Live" : status === "connecting" ? "Connecting" : "Offline";

  return (
    <div className="flex items-center gap-2 text-xs text-slate" title={label}>
      <span className={`inline-block h-2 w-2 rounded-full ${colour}`} aria-hidden />
      <span>{label}</span>
    </div>
  );
}
