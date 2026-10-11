"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { RiskSparkline } from "@/components/risk-sparkline";
import { VerdictBadge } from "@/components/verdict-badge";
import { fetchMe, fetchScans, storedBearer, type Caller } from "@/lib/api";
import type { Decision } from "@promptshield/shared-types";

type ScanRow = {
  scan_id: string;
  decision: Decision;
  risk: number;
  attack_types?: string[];
  latency_ms?: { total?: number };
  degraded?: string[];
  findings?: { detector?: string; reason_code?: string | null }[];
  safe_alternative?: string | null;
};

export default function PortalPage() {
  const [me, setMe] = useState<Caller | null>(null);
  const [scans, setScans] = useState<ScanRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState(0);

  useEffect(() => {
    if (!storedBearer()) return;
    Promise.all([fetchMe(), fetchScans(50)])
      .then(([caller, body]) => {
        setMe(caller);
        const items = Array.isArray(body?.items) ? body.items : [];
        setScans(
          items.map((item: ScanRow) => ({
            scan_id: String(item.scan_id),
            decision: item.decision,
            risk: Number(item.risk),
            attack_types: item.attack_types ?? [],
            latency_ms: item.latency_ms,
            degraded: item.degraded ?? [],
            findings: item.findings ?? [],
            safe_alternative: item.safe_alternative ?? null,
          })),
        );
      })
      .catch((e) => setError(String(e)));
  }, []);

  const blocked = scans.filter((scan) => scan.decision === "block").length;
  const sanitised = scans.filter((scan) => scan.decision === "sanitize").length;
  const p95 =
    scans.length === 0
      ? null
      : [...scans.map((scan) => scan.latency_ms?.total ?? 0)].sort((a, b) => a - b)[
          Math.min(scans.length - 1, Math.floor(scans.length * 0.95))
        ];
  const judgeUse =
    scans.length === 0
      ? null
      : scans.filter((scan) =>
          (scan.findings ?? []).some(
            (finding) => finding.detector === "judge" || String(finding.reason_code || "").startsWith("JUDGE_"),
          ),
        ).length / scans.length;
  const active = scans[selected] ?? null;

  return (
    <div className="min-w-0 space-y-4 p-4 md:p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Your scans</h1>
        <p className="text-sm text-slate">
          {me
            ? `${me.name || "Caller"} · key ${me.prefix || "—"}… · ${me.scan_count} scan${me.scan_count === 1 ? "" : "s"}`
            : "Sign in to see the scans on your account."}
        </p>
      </header>

      {error ? <p className="text-sm text-block">{error}</p> : null}

      {!me ? (
        <p className="text-sm text-slate">
          <Link href="/login" className="text-uv hover:underline">
            Sign in
          </Link>{" "}
          or{" "}
          <Link href="/signup" className="text-uv hover:underline">
            create an account
          </Link>
          .
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-5" data-testid="portal-kpis">
            {[
              ["Scans (window)", String(scans.length)],
              ["Blocked", scans.length ? `${((blocked / scans.length) * 100).toFixed(1)}%` : "—"],
              ["Sanitised", scans.length ? `${((sanitised / scans.length) * 100).toFixed(1)}%` : "—"],
              ["p95", p95 != null ? `${Math.round(p95)} ms` : "—"],
              ["Judge use", judgeUse != null ? `${(judgeUse * 100).toFixed(0)}%` : "—"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-panel border border-rule bg-surface p-4">
                <div className="text-xs text-slate">{label}</div>
                <div className="mt-1 font-mono text-xl font-medium">{value}</div>
              </div>
            ))}
          </div>

          <RiskSparkline points={scans.map((scan) => ({ risk: scan.risk, decision: scan.decision, scanId: scan.scan_id }))} />

          <div className="grid gap-3 lg:grid-cols-[1fr_18rem]">
            <div className="max-h-[28rem] overflow-auto rounded-panel border border-rule bg-surface">
              <table className="w-full text-sm">
                <thead className="border-b border-rule text-left text-xs text-slate">
                  <tr>
                    <th className="px-3 py-2 font-medium">Verdict</th>
                    <th className="px-3 py-2 font-medium">Risk</th>
                    <th className="px-3 py-2 font-medium">Types</th>
                    <th className="px-3 py-2 font-medium">Scan</th>
                  </tr>
                </thead>
                <tbody>
                  {scans.map((scan, index) => (
                    <tr
                      key={scan.scan_id}
                      className={`cursor-pointer border-b border-rule last:border-0 ${index === selected ? "bg-uv/5" : ""}`}
                      onClick={() => setSelected(index)}
                    >
                      <td className="px-3 py-2">
                        <VerdictBadge decision={scan.decision} />
                      </td>
                      <td className="px-3 py-2 font-mono text-xs">{scan.risk.toFixed(2)}</td>
                      <td className="px-3 py-2 text-xs text-slate">{(scan.attack_types ?? []).slice(0, 2).join(", ") || "—"}</td>
                      <td className="px-3 py-2 font-mono text-xs">{scan.scan_id}</td>
                    </tr>
                  ))}
                  {scans.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="px-3 py-8 text-sm text-slate">
                        No scans for this account yet. Send a prompt to POST /v1/scan with your key.
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>

            <aside className="space-y-3 rounded-panel border border-rule bg-surface p-4">
              <h2 className="text-sm font-medium">Result</h2>
              {active ? (
                <>
                  <VerdictBadge decision={active.decision} />
                  <div className="space-y-1 font-mono text-xs text-slate">
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
                  <Link href={`/portal/scans/${active.scan_id}`} className="inline-block text-sm text-uv hover:underline">
                    Open X-ray
                  </Link>
                </>
              ) : (
                <p className="text-xs text-slate">Select a scan to see the verdict, then open X-ray for the document and findings.</p>
              )}
            </aside>
          </div>
        </>
      )}
    </div>
  );
}
