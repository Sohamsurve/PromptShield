"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { VerdictBadge } from "@/components/verdict-badge";
import { fetchScans } from "@/lib/api";
import type { Decision } from "@promptshield/shared-types";

type ScanRow = {
  scan_id: string;
  decision: Decision;
  risk: number;
  attack_types?: string[];
};

export default function ScansPage() {
  const [items, setItems] = useState<ScanRow[]>([]);
  const [q, setQ] = useState("");

  useEffect(() => {
    fetchScans(100)
      .then((d) => setItems(d.items ?? []))
      .catch(() => setItems([]));
  }, []);

  const filtered = items.filter(
    (s) =>
      !q ||
      s.scan_id.includes(q) ||
      s.decision.includes(q) ||
      (s.attack_types ?? []).some((t) => t.includes(q)),
  );

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Scans</h1>
        <p className="text-slate text-sm mt-1">Search, filter, open X-ray.</p>
      </div>
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Search scan id, decision, attack type…"
        className="w-full max-w-md rounded-panel border border-rule bg-surface px-3 py-2 text-sm"
      />
      <ul className="space-y-2">
        {filtered.map((s) => (
          <li key={s.scan_id}>
            <Link
              href={`/scans/${s.scan_id}`}
              className="flex flex-wrap items-center gap-3 rounded-panel border border-rule bg-surface px-3 py-2 hover:border-uv"
            >
              <VerdictBadge decision={s.decision} />
              <span className="font-mono text-xs">{s.scan_id}</span>
              <span className="font-mono text-xs text-slate">{s.risk.toFixed(2)}</span>
              <span className="text-xs text-slate">{(s.attack_types ?? []).join(", ")}</span>
            </Link>
          </li>
        ))}
        {!filtered.length ? <li className="text-sm text-slate">No matching scans.</li> : null}
      </ul>
    </div>
  );
}
