"use client";

import { useEffect, useState } from "react";

/** One-shot UV beam; respects prefers-reduced-motion. */
export function UVSweep({ active = true }: { active?: boolean }) {
  const [show, setShow] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!active || done) return;
    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setDone(true);
      return;
    }
    setShow(true);
    const t = window.setTimeout(() => {
      setShow(false);
      setDone(true);
    }, 900);
    return () => window.clearTimeout(t);
  }, [active, done]);

  if (!show) return null;
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-[var(--uv)] opacity-80 animate-[uvbeam_900ms_ease-out_forwards]"
      style={{
        boxShadow: "0 0 24px 8px color-mix(in srgb, var(--uv) 45%, transparent)",
      }}
    />
  );
}
