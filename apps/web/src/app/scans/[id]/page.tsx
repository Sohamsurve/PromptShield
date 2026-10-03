"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { VerdictBadge } from "@/components/verdict-badge";
import { UVSweep } from "@/components/uv-sweep";
import { apiBase, fetchScan } from "@/lib/api";
import type { Decision } from "@promptshield/shared-types";

type Finding = {
  id: string;
  reason_code?: string;
  score?: number;
  evidence?: string;
  attack_types?: string[];
  rule_id?: string | null;
  span?: [number, number] | null;
};

type Scan = {
  scan_id: string;
  decision: Decision;
  risk: number;
  policy_version?: string;
  attack_types?: string[];
  findings?: Finding[];
  sanitized_text?: string | null;
  spotlighted_text?: string | null;
  latency_ms?: Record<string, number>;
  segments?: Array<{ text?: string; canonical?: string }>;
  degraded?: string[];
};

type View = "original" | "revealed" | "sanitised" | "spotlighted";

function renderWithInvisibleChips(text: string) {
  const parts: React.ReactNode[] = [];
  let buf = "";
  const flush = () => {
    if (buf) {
      parts.push(buf);
      buf = "";
    }
  };
  for (const ch of text) {
    const code = ch.codePointAt(0) ?? 0;
    const invisible =
      code === 0x200b ||
      code === 0x200c ||
      code === 0x200d ||
      code === 0xfeff ||
      (code >= 0x202a && code <= 0x202e) ||
      (code >= 0xe0001 && code <= 0xe007f);
    if (invisible) {
      flush();
      parts.push(
        <span
          key={`${parts.length}-${code}`}
          className="mx-0.5 inline-flex rounded-chip border border-rule bg-paper px-1 font-mono text-[10px] text-uv"
        >
          ⟨U+{code.toString(16).toUpperCase()}⟩
        </span>,
      );
    } else {
      buf += ch;
    }
  }
  flush();
  return parts;
}

export default function XRayPage() {
  const params = useParams<{ id: string }>();
  const [scan, setScan] = useState<Scan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View>("revealed");
  const [activeFinding, setActiveFinding] = useState<string | null>(null);

  useEffect(() => {
    if (!params?.id) return;
    fetchScan(params.id)
      .then(setScan)
      .catch((e) => setError(String(e)));
  }, [params?.id]);

  const docText = useMemo(() => {
    if (!scan) return "";
    if (view === "sanitised") return scan.sanitized_text || "";
    if (view === "spotlighted") return scan.spotlighted_text || scan.sanitized_text || "";
    const joined = (scan.segments ?? []).map((s) => s.text || "").join("\n");
    return joined || scan.sanitized_text || "";
  }, [scan, view]);

  if (error) {
    return (
      <div className="p-6">
        <p className="text-block text-sm">
          {error}. API at {apiBase()}.
        </p>
      </div>
    );
  }
  if (!scan) {
    return (
      <div className="p-6 text-slate text-sm">Loading scan…</div>
    );
  }

  const stages = [
    ["Extract", scan.latency_ms?.adapt],
    ["Normalise", scan.latency_ms?.signatures ? 1 : undefined],
    ["Detect", scan.latency_ms?.signatures],
    ["Fuse", 1],
    ["Neutralise", scan.latency_ms?.judge],
    ["Log", scan.latency_ms?.total],
  ] as const;

  return (
    <div className="p-4 md:p-6 space-y-4">
      <header className="flex flex-col md:flex-row md:items-center gap-3 justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl font-bold font-mono tracking-tight">{scan.scan_id}</h1>
            <VerdictBadge decision={scan.decision} />
            <span className="text-sm text-slate font-mono">risk {scan.risk.toFixed(2)}</span>
            <span className="text-xs text-slate">policy v{scan.policy_version ?? "—"}</span>
          </div>
          {(scan.degraded ?? []).length ? (
            <p className="text-xs text-sanitize mt-1">Degraded: {scan.degraded?.join(", ")}</p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-1" role="tablist" aria-label="Document view">
          {(["original", "revealed", "sanitised", "spotlighted"] as View[]).map((v) => (
            <button
              key={v}
              type="button"
              role="tab"
              aria-selected={view === v}
              onClick={() => setView(v)}
              className={`rounded-panel px-2.5 py-1 text-xs capitalize border ${
                view === v ? "border-uv text-uv bg-surface" : "border-rule text-slate bg-surface"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
      </header>

      <div className="grid lg:grid-cols-[1.4fr_1fr] gap-3">
        <section className="relative rounded-panel border border-rule bg-surface p-4 min-h-[280px] overflow-hidden">
          <UVSweep />
          <h2 className="text-sm font-medium mb-2">Document</h2>
          <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-relaxed text-ink max-w-[72ch]">
            {renderWithInvisibleChips(docText || "(empty)")}
          </pre>
        </section>

        <section className="rounded-panel border border-rule bg-surface p-4">
          <h2 className="text-sm font-medium mb-2">Findings ({scan.findings?.length ?? 0})</h2>
          <ul className="space-y-2">
            {(scan.findings ?? []).map((f) => (
              <li key={f.id}>
                <button
                  type="button"
                  onClick={() => setActiveFinding(f.id)}
                  className={`w-full text-left rounded-panel border px-2 py-2 ${
                    activeFinding === f.id ? "border-uv" : "border-rule"
                  }`}
                >
                  <div className="flex justify-between gap-2 text-sm">
                    <span className="font-mono text-uv">{f.reason_code ?? "FINDING"}</span>
                    <span className="font-mono text-slate">{(f.score ?? 0).toFixed(2)}</span>
                  </div>
                  <div className="text-xs text-slate mt-1">
                    {(f.attack_types ?? []).join(", ") || "—"}
                    {f.rule_id ? ` · ${f.rule_id}` : ""}
                  </div>
                  {f.evidence ? (
                    <div className="mt-1 font-mono text-[11px] text-ink line-clamp-2">{f.evidence}</div>
                  ) : null}
                </button>
              </li>
            ))}
            {!scan.findings?.length ? <li className="text-sm text-slate">No findings.</li> : null}
          </ul>
        </section>
      </div>

      <ol className="flex flex-wrap gap-2 text-xs font-mono">
        {stages.map(([label, ms], i) => (
          <li key={label} className="rounded-panel border border-rule bg-surface px-2 py-1.5">
            <span className="text-uv mr-1">{i + 1}</span>
            {label}
            {ms != null ? <span className="text-slate"> {Math.round(ms)}ms</span> : null}
          </li>
        ))}
      </ol>
    </div>
  );
}
