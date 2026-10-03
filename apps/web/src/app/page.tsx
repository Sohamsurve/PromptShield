"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { VerdictBadge } from "@/components/verdict-badge";
import { apiBase, fetchScans } from "@/lib/api";
import type { Decision } from "@promptshield/shared-types";

type ScanRow = {
  scan_id: string;
  decision: Decision;
  risk: number;
  attack_types?: string[];
  latency_ms?: { total?: number };
  degraded?: string[];
};

export default function ConsolePage() {
  const [items, setItems] = useState<ScanRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [paused, setPaused] = useState(false);

  useEffect(() => {
    if (paused) return;
    let alive = true;
    const load = () =>
      fetchScans(40)
        .then((data) => {
          if (alive) setItems(data.items ?? []);
        })
        .catch((e) => {
          if (alive) setError(String(e));
        });
    load();
    const t = window.setInterval(load, 4000);
    return () => {
      alive = false;
      window.clearInterval(t);
    };
  }, [paused]);

  const blocked = items.filter((s) => s.decision === "block").length;
  const sanitised = items.filter((s) => s.decision === "sanitize").length;
  const p95 =
    items.length === 0
      ? null
      : [...items.map((s) => s.latency_ms?.total ?? 0)].sort((a, b) => a - b)[
          Math.min(items.length - 1, Math.floor(items.length * 0.95))
        ];

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Console</h1>
          <p className="text-slate text-sm mt-1 max-w-prose">
            Live view of traffic and decisions.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setPaused((p) => !p)}
          className="rounded-panel border border-rule bg-surface px-3 py-1.5 text-sm self-start"
        >
          {paused ? "Resume" : "Pause"}
        </button>
      </div>

      {error ? (
        <p className="text-sm text-block">
          {error}. Start the API at {apiBase()}, or run a fixture in the Arena.
        </p>
      ) : null}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          ["Scans (window)", String(items.length)],
          ["Blocked", items.length ? `${((blocked / items.length) * 100).toFixed(1)}%` : "—"],
          ["Sanitised", items.length ? `${((sanitised / items.length) * 100).toFixed(1)}%` : "—"],
          ["p95", p95 != null ? `${Math.round(p95)} ms` : "—"],
        ].map(([label, value]) => (
          <div key={label} className="rounded-panel border border-rule bg-surface p-4">
            <div className="text-xs text-slate">{label}</div>
            <div className="text-xl font-medium mt-1 font-mono">{value}</div>
          </div>
        ))}
      </div>

      <div className="rounded-panel border border-rule bg-surface overflow-hidden">
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-slate border-b border-rule">
            <tr>
              <th className="px-3 py-2 font-medium">Verdict</th>
              <th className="px-3 py-2 font-medium">Risk</th>
              <th className="px-3 py-2 font-medium">Types</th>
              <th className="px-3 py-2 font-medium">Scan</th>
            </tr>
          </thead>
          <tbody>
            {items.map((s) => (
              <tr key={s.scan_id} className="border-b border-rule last:border-0">
                <td className="px-3 py-2">
                  <VerdictBadge decision={s.decision} />
                </td>
                <td className="px-3 py-2 font-mono text-xs">{s.risk.toFixed(2)}</td>
                <td className="px-3 py-2 text-xs text-slate">
                  {(s.attack_types ?? []).slice(0, 2).join(", ") || "—"}
                </td>
                <td className="px-3 py-2">
                  <Link href={`/scans/${s.scan_id}`} className="font-mono text-xs text-uv hover:underline">
                    {s.scan_id}
                  </Link>
                </td>
              </tr>
            ))}
            {!items.length ? (
              <tr>
                <td colSpan={4} className="px-3 py-8 text-slate text-sm">
                  No scans yet. Run a fixture in the Arena or send content to POST /v1/scan.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
