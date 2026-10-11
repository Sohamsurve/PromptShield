"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { RiskSparkline } from "@/components/risk-sparkline";
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
  source_type?: string;
  findings?: { detector?: string; reason_code?: string | null }[];
  safe_alternative?: string | null;
};

const DECISIONS = ["", "allow", "sanitize", "quarantine", "block", "escalate"] as const;

export default function ConsolePage() {
  const router = useRouter();
  const [items, setItems] = useState<ScanRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [paused, setPaused] = useState(false);
  const [decision, setDecision] = useState("");
  const [source, setSource] = useState("");
  const [attack, setAttack] = useState("");
  const [q, setQ] = useState("");
  const [selected, setSelected] = useState(0);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const filterRef = useRef<HTMLInputElement>(null);

  const load = useCallback(() => {
    fetchScans(40)
      .then((data) => {
        setItems(data.items ?? []);
        setError(null);
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (paused) return;
    load();
    const t = window.setInterval(load, 4000);
    return () => window.clearInterval(t);
  }, [paused, load]);

  const filtered = useMemo(() => {
    return items.filter((s) => {
      if (decision && s.decision !== decision) return false;
      if (source && !(s.source_type || "").includes(source)) return false;
      if (attack && !(s.attack_types ?? []).some((t) => t.includes(attack))) return false;
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
  }, [items, decision, source, attack, q]);

  useEffect(() => {
    if (selected >= filtered.length) setSelected(Math.max(0, filtered.length - 1));
  }, [filtered.length, selected]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") {
        if (e.key === "Escape") (e.target as HTMLElement).blur();
        return;
      }
      if (e.key === "p") {
        e.preventDefault();
        setPaused((p) => !p);
      } else if (e.key === "/") {
        e.preventDefault();
        filterRef.current?.focus();
      } else if (e.key === "j") {
        e.preventDefault();
        setSelected((i) => Math.min(filtered.length - 1, i + 1));
      } else if (e.key === "k") {
        e.preventDefault();
        setSelected((i) => Math.max(0, i - 1));
      } else if (e.key === "Enter") {
        e.preventDefault();
        setDrawerOpen(true);
      } else if (e.key === "x" && filtered[selected]) {
        e.preventDefault();
        router.push(`/scans/${filtered[selected].scan_id}`);
      } else if (e.key === "Escape") {
        setDrawerOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [filtered, selected, router]);

  const blocked = items.filter((s) => s.decision === "block").length;
  const sanitised = items.filter((s) => s.decision === "sanitize").length;
  const p95 =
    items.length === 0
      ? null
      : [...items.map((s) => s.latency_ms?.total ?? 0)].sort((a, b) => a - b)[
          Math.min(items.length - 1, Math.floor(items.length * 0.95))
        ];
  const judgeUse =
    items.length === 0
      ? null
      : items.filter((s) =>
          (s.findings ?? []).some(
            (f) => f.detector === "judge" || String(f.reason_code || "").startsWith("JUDGE_"),
          ),
        ).length / items.length;
  const degradedAny = items.some((s) => (s.degraded ?? []).length > 0);
  const active = filtered[selected] ?? null;

  return (
    <div className="p-4 md:p-6 space-y-4" data-testid="console-page">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Console</h1>
          <p className="text-slate text-sm mt-1 max-w-prose">
            Live view of traffic and decisions. Keys: j/k move, Enter drawer, x X-ray, / filter, p pause.
          </p>
        </div>
        <button
          type="button"
          data-testid="console-pause"
          onClick={() => setPaused((p) => !p)}
          className="rounded-panel border border-rule bg-surface px-3 py-1.5 text-sm self-start"
        >
          {paused ? "Resume" : "Pause"}
        </button>
      </div>

      {degradedAny ? (
        <p className="text-sm text-sanitize border border-rule rounded-panel px-3 py-2 bg-surface" data-testid="console-degraded">
          Degraded scan events present in this window — see X-ray for details.
        </p>
      ) : null}

      {error ? (
        <p className="text-sm text-block">
          {error}. Start the API at {apiBase()}, or run a fixture in the Arena.
        </p>
      ) : null}

      <div className="grid grid-cols-2 md:grid-cols-5 gap-3" data-testid="console-kpis">
        {[
          ["Scans (window)", String(items.length)],
          ["Blocked", items.length ? `${((blocked / items.length) * 100).toFixed(1)}%` : "—"],
          ["Sanitised", items.length ? `${((sanitised / items.length) * 100).toFixed(1)}%` : "—"],
          ["p95", p95 != null ? `${Math.round(p95)} ms` : "—"],
          ["Judge use", judgeUse != null ? `${(judgeUse * 100).toFixed(0)}%` : "—"],
        ].map(([label, value]) => (
          <div key={label} className="rounded-panel border border-rule bg-surface p-4">
            <div className="text-xs text-slate">{label}</div>
            <div className="text-xl font-medium mt-1 font-mono">{value}</div>
          </div>
        ))}
      </div>
      <RiskSparkline
        testId="console-sparkline"
        points={items.map((scan) => ({ risk: scan.risk, decision: scan.decision, scanId: scan.scan_id }))}
      />

      <div className="flex flex-wrap gap-2 items-center" data-testid="console-filters">
        <select
          aria-label="Filter decision"
          value={decision}
          onChange={(e) => setDecision(e.target.value)}
          className="rounded-panel border border-rule bg-surface px-2 py-1.5 text-sm"
        >
          <option value="">Decision</option>
          {DECISIONS.filter(Boolean).map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
        <select
          aria-label="Filter source"
          value={source}
          onChange={(e) => setSource(e.target.value)}
          className="rounded-panel border border-rule bg-surface px-2 py-1.5 text-sm"
        >
          <option value="">Source</option>
          {["text", "html", "pdf", "email", "markdown", "image"].map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <input
          aria-label="Filter attack type"
          value={attack}
          onChange={(e) => setAttack(e.target.value)}
          placeholder="attack type…"
          className="rounded-panel border border-rule bg-surface px-2 py-1.5 text-sm w-36"
        />
        <input
          ref={filterRef}
          data-testid="console-search"
          aria-label="Search scans"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="search…"
          className="rounded-panel border border-rule bg-surface px-2 py-1.5 text-sm flex-1 min-w-[10rem]"
        />
      </div>

      <div className="grid lg:grid-cols-[1fr_18rem] gap-3">
        <div className="rounded-panel border border-rule bg-surface overflow-auto max-h-[28rem]" data-testid="console-feed-scroll">
          <table className="w-full text-sm" data-testid="console-feed">
            <thead className="text-left text-xs text-slate border-b border-rule">
              <tr>
                <th className="px-3 py-2 font-medium">Verdict</th>
                <th className="px-3 py-2 font-medium">Risk</th>
                <th className="px-3 py-2 font-medium">Types</th>
                <th className="px-3 py-2 font-medium">Scan</th>
              </tr>
            </thead>
            <tbody>
              {loading
                ? Array.from({ length: 4 }).map((_, i) => (
                    <tr key={i} data-testid="console-skeleton">
                      <td colSpan={4} className="px-3 py-3">
                        <div className="h-4 bg-rule/40 rounded animate-pulse" />
                      </td>
                    </tr>
                  ))
                : null}
              {!loading &&
                filtered.map((s, idx) => (
                  <tr
                    key={s.scan_id}
                    data-testid={`console-row-${s.scan_id}`}
                    className={`border-b border-rule last:border-0 cursor-pointer ${
                      idx === selected ? "bg-uv/5" : ""
                    }`}
                    onClick={() => {
                      setSelected(idx);
                      setDrawerOpen(true);
                    }}
                  >
                    <td className="px-3 py-2">
                      <VerdictBadge decision={s.decision} />
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{s.risk.toFixed(2)}</td>
                    <td className="px-3 py-2 text-xs text-slate">
                      {(s.attack_types ?? []).slice(0, 2).join(", ") || "—"}
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{s.scan_id}</td>
                  </tr>
                ))}
              {!loading && !filtered.length ? (
                <tr>
                  <td colSpan={4} className="px-3 py-8 text-slate text-sm" data-testid="console-empty">
                    No scans yet. Run a fixture in the Arena or send content to POST /v1/scan.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>

        <aside
          className={`rounded-panel border border-rule bg-surface p-4 space-y-3 ${drawerOpen ? "" : "opacity-80"}`}
          data-testid="console-drawer"
        >
          <h2 className="text-sm font-medium">Detail</h2>
          {active && drawerOpen ? (
            <>
              <VerdictBadge decision={active.decision} />
              <div className="text-xs font-mono space-y-1 text-slate">
                <div>{active.scan_id}</div>
                <div>risk {active.risk.toFixed(2)}</div>
                <div>{(active.attack_types ?? []).join(", ") || "—"}</div>
              </div>
              {active.safe_alternative ? (
                <p className="text-sm">
                  <span className="font-medium">Safe alternative. </span>
                  {active.safe_alternative}
                </p>
              ) : null}
              <Link
                href={`/scans/${active.scan_id}`}
                className="inline-block text-sm text-uv hover:underline"
                data-testid="console-open-xray"
              >
                Open X-ray
              </Link>
            </>
          ) : (
            <p className="text-xs text-slate">Select a row (Enter) for verdict and findings.</p>
          )}
        </aside>
      </div>
    </div>
  );
}
