"use client";

import { useEffect, useState } from "react";
import { CoverageHeatmap } from "@/components/coverage-heatmap";
import { apiBase, fetchEvalLatest, fetchHealthz } from "@/lib/api";

type Cell = { n?: number; recall?: number; ci?: [number, number] };
type Heatmap = { rows: string[]; cols: string[]; cells: Record<string, Record<string, Cell>> };

type Report = {
  heatmap?: Heatmap;
  text_phase1?: { fpr?: number; hard_negative_fpr?: number; acted_fpr?: number; flagged_fpr?: number };
  phase3?: { hard_negative_fpr?: number };
  acted?: { fpr?: number };
  flagged?: { fpr?: number };
};

export default function CoveragePage() {
  const [heatmap, setHeatmap] = useState<Heatmap | null>(null);
  const [fpr, setFpr] = useState<{ benign?: number; hard?: number }>({});
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<{ row: string; col: string; cell: Cell } | null>(null);
  const [metric, setMetric] = useState<"acted" | "flagged">("acted");
  const [judgeMode, setJudgeMode] = useState<string>("—");

  useEffect(() => {
    fetchEvalLatest()
      .then((data: Report) => {
        setHeatmap(data.heatmap ?? null);
        const useActed = true; // initial; toggled below via report fields
        void useActed;
        setFpr({
          benign: data.acted?.fpr ?? data.text_phase1?.acted_fpr ?? data.text_phase1?.fpr,
          hard: data.phase3?.hard_negative_fpr ?? data.text_phase1?.hard_negative_fpr,
        });
      })
      .catch((e) => setError(String(e)));
    fetchHealthz()
      .then((h) => setJudgeMode(h.judge_mode ?? "—"))
      .catch(() => setJudgeMode("—"));
  }, []);

  useEffect(() => {
    fetchEvalLatest()
      .then((data: Report) => {
        setFpr({
          benign:
            metric === "acted"
              ? data.acted?.fpr ?? data.text_phase1?.acted_fpr ?? data.text_phase1?.fpr
              : data.flagged?.fpr ?? data.text_phase1?.flagged_fpr ?? data.text_phase1?.fpr,
          hard: data.phase3?.hard_negative_fpr ?? data.text_phase1?.hard_negative_fpr,
        });
      })
      .catch(() => undefined);
  }, [metric]);

  const fprPass = fpr.benign == null ? null : fpr.benign <= 0.02;

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Coverage</h1>
          <p className="text-slate text-sm mt-1 max-w-prose">
            Attack-type × format recall. Headline: <span className="font-mono">ACTED</span>. Gallery fixtures are{" "}
            <span className="font-mono">in-sample</span>. Cells with n &lt; 10 are hatched as insufficient.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <label className="flex items-center gap-2 border border-rule rounded-panel px-2 py-1.5 bg-surface">
            <span className="text-slate">Metric</span>
            <select
              className="bg-transparent font-mono"
              value={metric}
              onChange={(e) => setMetric(e.target.value as "acted" | "flagged")}
            >
              <option value="acted">ACTED</option>
              <option value="flagged">FLAGGED</option>
            </select>
          </label>
          <span className="font-mono text-xs border border-rule rounded-panel px-2 py-1.5 bg-surface">
            judge: {judgeMode}
          </span>
        </div>
      </div>

      {error ? (
        <p className="text-sm text-block">
          {error}. Run <span className="font-mono">make eval-fast</span> then ensure the API can read{" "}
          <span className="font-mono">eval/reports/latest</span> ({apiBase()}).
        </p>
      ) : null}

      <div className="grid sm:grid-cols-3 gap-3">
        <div className="rounded-panel border border-rule bg-surface p-4">
          <div className="text-xs text-slate">{metric === "acted" ? "ACTED" : "FLAGGED"} FPR benign</div>
          <div className="mt-1 text-xl font-mono">{fpr.benign == null ? "—" : fpr.benign.toFixed(3)}</div>
          <div className={`mt-2 text-sm ${fprPass ? "text-allow" : fprPass === false ? "text-block" : "text-slate"}`}>
            {fprPass == null ? "—" : fprPass ? "MET ≤0.02" : "NOT MET ≤0.02"}
          </div>
        </div>
        <div className="rounded-panel border border-rule bg-surface p-4">
          <div className="text-xs text-slate">Hard-negative FPR</div>
          <div className="mt-1 text-xl font-mono">{fpr.hard == null ? "—" : fpr.hard.toFixed(3)}</div>
          <div className="mt-2 text-sm text-slate">reported</div>
        </div>
        <div className="rounded-panel border border-rule bg-surface p-4">
          <div className="text-xs text-slate">Independent F / D</div>
          <div className="mt-1 text-xl font-mono">—</div>
          <div className="mt-2 text-sm text-slate">not evaluated</div>
        </div>
      </div>

      <div className="grid lg:grid-cols-[1fr_16rem] gap-3">
        <div className="rounded-panel border border-rule bg-surface p-3">
          {heatmap ? (
            <CoverageHeatmap data={heatmap} onSelect={(row, col, cell) => setSelected({ row, col, cell })} />
          ) : (
            <p className="text-sm text-slate p-4">Loading heatmap…</p>
          )}
        </div>
        <aside className="rounded-panel border border-rule bg-surface p-4 space-y-3">
          <h2 className="text-sm font-medium">Cell detail</h2>
          {selected ? (
            <div className="text-xs font-mono space-y-1">
              <div className="text-slate">Selected</div>
              <div>
                {selected.row} × {selected.col}
              </div>
              <div>recall {(selected.cell.recall ?? 0).toFixed(2)}</div>
              <div>n={selected.cell.n ?? 0}</div>
              {selected.cell.ci ? (
                <div>
                  CI [{selected.cell.ci[0].toFixed(2)}, {selected.cell.ci[1].toFixed(2)}]
                </div>
              ) : null}
            </div>
          ) : (
            <p className="text-xs text-slate">Click a cell for Wilson CI.</p>
          )}
        </aside>
      </div>
    </div>
  );
}
