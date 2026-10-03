"use client";

type Cell = { n?: number; recall?: number; ci?: [number, number] };
type Heatmap = {
  rows: string[];
  cols: string[];
  cells: Record<string, Record<string, Cell>>;
};

function cellColour(recall: number | undefined, n: number) {
  if (!n) return "var(--rule)";
  if (recall == null) return "var(--rule)";
  // sequential, colour-blind-safer: ink → uv → allow
  if (recall >= 0.9) return "color-mix(in srgb, var(--allow) 70%, var(--surface))";
  if (recall >= 0.7) return "color-mix(in srgb, var(--uv) 45%, var(--surface))";
  if (recall >= 0.4) return "color-mix(in srgb, var(--sanitize) 40%, var(--surface))";
  return "color-mix(in srgb, var(--block) 35%, var(--surface))";
}

export function CoverageHeatmap({
  data,
  onSelect,
}: {
  data: Heatmap;
  onSelect?: (row: string, col: string, cell: Cell) => void;
}) {
  const cols = data.cols.length ? data.cols : ["text"];
  return (
    <div className="overflow-x-auto">
      <table className="border-collapse text-[11px] font-mono min-w-full">
        <thead>
          <tr>
            <th className="p-1 text-left text-slate font-medium sticky left-0 bg-surface">type \\ fmt</th>
            {cols.map((c) => (
              <th key={c} className="p-1 text-slate font-medium whitespace-nowrap">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((row) => (
            <tr key={row}>
              <th className="p-1 text-left text-ink font-medium sticky left-0 bg-surface whitespace-nowrap">
                {row}
              </th>
              {cols.map((col) => {
                const cell = data.cells?.[row]?.[col] ?? {};
                const n = cell.n ?? 0;
                const recall = cell.recall;
                const insufficient = n > 0 && n < 10;
                const title =
                  n === 0
                    ? "no samples"
                    : `recall ${(recall ?? 0).toFixed(2)} · n=${n}` +
                      (cell.ci ? ` · CI [${cell.ci[0].toFixed(2)}, ${cell.ci[1].toFixed(2)}]` : "");
                return (
                  <td key={col} className="p-0.5">
                    <button
                      type="button"
                      title={title}
                      onClick={() => onSelect?.(row, col, cell)}
                      className="w-[4.5rem] h-12 rounded-chip border border-rule flex flex-col items-center justify-center relative"
                      style={{
                        background: cellColour(recall, n),
                        backgroundImage: insufficient
                          ? "repeating-linear-gradient(45deg, transparent, transparent 3px, color-mix(in srgb, var(--ink) 12%, transparent) 3px, color-mix(in srgb, var(--ink) 12%, transparent) 6px)"
                          : undefined,
                      }}
                    >
                      {n === 0 ? (
                        <span className="text-slate">—</span>
                      ) : (
                        <>
                          <span className="text-ink font-medium">{(recall ?? 0).toFixed(2)}</span>
                          <span className="text-slate">n={n}</span>
                          {insufficient ? <span className="text-[9px] text-slate">insuff.</span> : null}
                        </>
                      )}
                    </button>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
