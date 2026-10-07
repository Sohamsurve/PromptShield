"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
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

type SegmentSummary = {
  id?: string;
  hidden?: boolean;
  hidden_reason?: string | null;
  text_preview?: string;
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
  segments?: SegmentSummary[];
  degraded?: string[];
};

type View = "original" | "revealed" | "sanitised" | "spotlighted";

function renderWithInvisibleChips(text: string) {
  const parts: ReactNode[] = [];
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

function renderWithHighlights(
  text: string,
  highlight: [number, number] | null,
  hiddenRanges: Array<[number, number]>,
) {
  if (!text) return "(empty)";
  const marks: Array<{ lo: number; hi: number; kind: "finding" | "hidden" }> = [];
  if (highlight && highlight[0] < highlight[1]) {
    marks.push({ lo: highlight[0], hi: highlight[1], kind: "finding" });
  }
  for (const [lo, hi] of hiddenRanges) {
    if (lo < hi) marks.push({ lo, hi, kind: "hidden" });
  }
  marks.sort((a, b) => a.lo - b.lo || (a.kind === "finding" ? -1 : 1));
  if (!marks.length) return renderWithInvisibleChips(text);

  const nodes: ReactNode[] = [];
  let cursor = 0;
  const pushPlain = (end: number) => {
    if (end > cursor) {
      nodes.push(
        <span key={`p-${cursor}`}>{renderWithInvisibleChips(text.slice(cursor, end))}</span>,
      );
      cursor = end;
    }
  };
  for (const m of marks) {
    const lo = Math.max(0, Math.min(m.lo, text.length));
    const hi = Math.max(lo, Math.min(m.hi, text.length));
    pushPlain(lo);
    const slice = text.slice(lo, hi);
    if (m.kind === "finding") {
      nodes.push(
        <mark key={`f-${lo}`} className="bg-[color-mix(in_srgb,var(--uv)_35%,transparent)] rounded-sm">
          {renderWithInvisibleChips(slice)}
        </mark>,
      );
    } else {
      nodes.push(
        <span
          key={`h-${lo}`}
          className="bg-[color-mix(in_srgb,var(--sanitize)_22%,transparent)] rounded-sm"
          title="Hidden / metadata segment"
        >
          {renderWithInvisibleChips(slice)}
        </span>,
      );
    }
    cursor = hi;
  }
  pushPlain(text.length);
  return nodes;
}

export function XRayClient({ scanId: scanIdProp }: { scanId?: string }) {
  const params = useParams<{ id: string }>();
  const scanId = scanIdProp ?? params?.id ?? "";
  const [scan, setScan] = useState<Scan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View>("revealed");
  const [activeFinding, setActiveFinding] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!scanId) {
      setLoading(false);
      setError("Missing scan id");
      return;
    }
    setLoading(true);
    setError(null);
    setScan(null);
    fetchScan(scanId)
      .then((data) => {
        if (!cancelled) setScan(data as Scan);
      })
      .catch((e) => {
        if (!cancelled) setError(String(e));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [scanId]);

  const activeSpan = useMemo((): [number, number] | null => {
    if (!scan || !activeFinding) return null;
    const f = scan.findings?.find((x) => x.id === activeFinding);
    return f?.span && f.span[0] < f.span[1] ? f.span : null;
  }, [scan, activeFinding]);

  const docText = useMemo(() => {
    if (!scan) return "";
    if (view === "sanitised") return scan.sanitized_text || "";
    if (view === "spotlighted") return scan.spotlighted_text || scan.sanitized_text || "";
    const joined = (scan.segments ?? []).map((s) => s.text_preview || "").join("\n");
    return joined || scan.sanitized_text || "";
  }, [scan, view]);

  const hiddenRanges = useMemo((): Array<[number, number]> => {
    if (!scan?.segments?.length || !docText) return [];
    const ranges: Array<[number, number]> = [];
    let off = 0;
    for (const seg of scan.segments) {
      const t = seg.text_preview || "";
      const len = t.length + 1;
      if (seg.hidden && t) {
        ranges.push([off, off + t.length]);
      }
      off += len;
    }
    return ranges;
  }, [scan, docText]);

  if (loading) {
    return (
      <div className="p-6 text-slate text-sm" role="status" aria-live="polite">
        Loading scan…
      </div>
    );
  }

  if (error) {
    const notFound = /404|not found|restarted/i.test(error);
    return (
      <div className="p-6 space-y-2">
        <p className="text-block text-sm">
          {notFound
            ? "Scan not found; the server may have restarted."
            : `Could not load scan: ${error}`}
        </p>
        <p className="text-xs text-slate">API: {apiBase()}</p>
      </div>
    );
  }

  if (!scan) {
    return (
      <div className="p-6">
        <p className="text-slate text-sm">Scan not found; the server may have restarted.</p>
      </div>
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

  const emptyDoc = !docText.trim();

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
          <UVSweep active={!emptyDoc} />
          <h2 className="text-sm font-medium mb-2">Document</h2>
          {emptyDoc ? (
            <p className="text-sm text-slate">Empty document for this view.</p>
          ) : (
            <pre className="whitespace-pre-wrap break-words font-mono text-xs leading-relaxed text-ink max-w-[72ch]">
              {renderWithHighlights(docText, activeSpan, hiddenRanges)}
            </pre>
          )}
        </section>

        <section className="rounded-panel border border-rule bg-surface p-4">
          <h2 className="text-sm font-medium mb-2">Findings ({scan.findings?.length ?? 0})</h2>
          <ul className="space-y-2">
            {(scan.findings ?? []).map((f) => (
              <li key={f.id}>
                <button
                  type="button"
                  onClick={() => setActiveFinding(f.id === activeFinding ? null : f.id)}
                  className={`w-full text-left rounded-panel border px-2 py-2 ${
                    activeFinding === f.id ? "border-uv ring-1 ring-uv/40" : "border-rule"
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
