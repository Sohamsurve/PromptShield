"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { VerdictBadge } from "@/components/verdict-badge";
import { FileDrop } from "@/components/file-drop";
import { fetchScans, postScan, postScanFile } from "@/lib/api";
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
  const [decision, setDecision] = useState("");
  const [paste, setPaste] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastId, setLastId] = useState<string | null>(null);

  const reload = useCallback(() => {
    fetchScans(100)
      .then((d) => setItems(d.items ?? []))
      .catch(() => setItems([]));
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  async function onPasteScan() {
    if (!paste.trim()) return;
    if (paste.length > 100_000) {
      setError("Content too large (100 KB max).");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const r = await postScan(paste.slice(0, 100_000), "text");
      setLastId(r.scan_id);
      setPaste("");
      reload();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onFile(file: File) {
    setBusy(true);
    setError(null);
    try {
      const r = await postScanFile(file);
      setLastId(r.scan_id);
      reload();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  const filtered = items.filter((s) => {
    if (decision && s.decision !== decision) return false;
    if (
      q &&
      !s.scan_id.includes(q) &&
      !s.decision.includes(q) &&
      !(s.attack_types ?? []).some((t) => t.includes(q))
    ) {
      return false;
    }
    return true;
  });

  return (
    <div className="p-4 md:p-6 space-y-4" data-testid="scans-page">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Scans</h1>
        <p className="text-slate text-sm mt-1">
          Paste text or upload a file, then open X-ray. Search prior decisions below.
        </p>
      </div>

      <section className="rounded-panel border border-rule bg-surface p-4 space-y-3 max-w-2xl" data-testid="scans-upload">
        <h2 className="text-sm font-medium">Scan content</h2>
        <textarea
          data-testid="scans-paste"
          value={paste}
          onChange={(e) => setPaste(e.target.value)}
          rows={6}
          placeholder="Paste a prompt, email body, or other text specimen…"
          className="w-full rounded-panel border border-rule bg-paper px-3 py-2 text-sm font-mono"
          disabled={busy}
        />
        <FileDrop disabled={busy} onFile={onFile} />
        <div className="flex flex-wrap gap-2 items-center">
          <button
            type="button"
            data-testid="scans-submit"
            disabled={busy || !paste.trim()}
            onClick={onPasteScan}
            className="rounded-panel bg-ink text-paper px-3 py-1.5 text-sm disabled:opacity-50"
          >
            Scan text
          </button>
          {lastId ? (
            <Link href={`/scans/${lastId}`} className="text-sm text-uv hover:underline">
              Open X-ray for {lastId}
            </Link>
          ) : null}
        </div>
        {error ? <p className="text-sm text-block">{error}</p> : null}
      </section>

      <div className="flex flex-wrap gap-2" data-testid="scans-filters">
        <select
          aria-label="Filter decision"
          value={decision}
          onChange={(e) => setDecision(e.target.value)}
          className="rounded-panel border border-rule bg-surface px-2 py-2 text-sm"
        >
          <option value="">All decisions</option>
          {["allow", "sanitize", "quarantine", "block", "escalate"].map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search scan id, decision, attack type…"
          className="w-full max-w-md rounded-panel border border-rule bg-surface px-3 py-2 text-sm"
        />
      </div>
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
        {!filtered.length ? (
          <li className="text-sm text-slate">
            No matching scans. Paste content above, drop a file, or run a fixture in the{" "}
            <Link href="/arena" className="text-uv underline">
              Arena
            </Link>
            .
          </li>
        ) : null}
      </ul>
    </div>
  );
}
