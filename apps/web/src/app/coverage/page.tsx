"use client";

import { useEffect, useState } from "react";
import { CoverageHeatmap } from "@/components/coverage-heatmap";
import { apiBase, fetchEvalLatest } from "@/lib/api";

type Cell = { n?: number; recall?: number; ci?: [number, number] };
type Heatmap = { rows: string[]; cols: string[]; cells: Record<string, Record<string, Cell>> };

export default function CoveragePage() {
  const [heatmap, setHeatmap] = useState<Heatmap | null>(null);
  const [fpr, setFpr] = useState<{ benign?: number; hard?: number }>({});
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<{ row: string; col: string; cell: Cell } | null>(null);

  useEffect(() => {
    fetchEvalLatest()
      .then((data) => {
        setHeatmap(data.heatmap ?? null);
        setFpr({
          benign: data.text_phase1?.fpr,
          hard: data.phase3?.hard_negative_fpr ?? data.text_phase1?.hard_negative_fpr,
        });
      })
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Coverage</h1>
        <p className="text-slate text-sm mt-1 max-w-prose">
          Attack-type × format recall. Cells with n &lt; 10 are hatched as insufficient.
        </p>
      </div>

      {error ? (
        <p className="text-sm text-block">
          {error}. Run <span className="font-mono">make eval-fast</span> then ensure the API can read{" "}
          <span className="font-mono">eval/reports/latest</span> ({apiBase()}).
        </p>
      ) : null}

      <div className="grid lg:grid-cols-[1fr_16rem] gap-3">
        <div className="rounded-panel border border-rule bg-surface p-3">
          {heatmap ? (
            <CoverageHeatmap data={heatmap} onSelect={(row, col, cell) => setSelected({ row, col, cell })} />
          ) : (
            <p className="text-sm text-slate p-4">Loading heatmap…</p>
          )}
        </div>
        <aside className="rounded-panel border border-rule bg-surface p-4 space-y-3">
          <h2 className="text-sm font-medium">FPR</h2>
          <div className="text-sm">
            <div className="flex justify-between">
              <span className="text-slate">Benign</span>
              <span className="font-mono">{fpr.benign == null ? "—" : fpr.benign.toFixed(3)}</span>
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-slate">Hard negative</span>
              <span className="font-mono">{fpr.hard == null ? "—" : fpr.hard.toFixed(3)}</span>
            </div>
          </div>
          {selected ? (
            <div className="border-t border-rule pt-3 text-xs font-mono space-y-1">
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
