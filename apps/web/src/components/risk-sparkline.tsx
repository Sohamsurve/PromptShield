const COLOR: Record<string, string> = {
  allow: "bg-allow",
  sanitize: "bg-sanitize",
  quarantine: "bg-quarantine",
  block: "bg-block",
  escalate: "bg-escalate",
};

const WORD: Record<string, string> = {
  allow: "Allowed",
  sanitize: "Sanitised",
  quarantine: "Quarantined",
  block: "Blocked",
  escalate: "Needs review",
};

export function RiskSparkline({
  points,
  testId,
}: {
  points: { risk: number; decision?: string; scanId?: string }[];
  testId?: string;
}) {
  const rows = points.slice(0, 36).reverse();
  return (
    <div
      className="flex h-16 items-stretch gap-1 overflow-visible rounded-panel border border-rule bg-surface px-3 py-2"
      data-testid={testId}
      aria-label="Risk over recent scans, oldest on the left"
    >
      {rows.length ? (
        rows.map((point, index) => {
          const risk = Math.min(1, Math.max(0, Number(point.risk) || 0));
          const height = Math.round(8 + risk * 32);
          const decision = point.decision || "allow";
          const word = WORD[decision] || decision;
          const place = index < 4 ? "left-0" : index > rows.length - 5 ? "right-0" : "left-1/2 -translate-x-1/2";
          return (
            <span key={point.scanId || index} className="group relative flex min-w-[4px] flex-1 flex-col justify-end bg-rule/35">
              <span
                role="tooltip"
                className={`pointer-events-none absolute bottom-full z-30 mb-2 hidden whitespace-nowrap rounded-panel border-2 border-ink bg-surface px-2 py-1 text-left shadow-[3px_3px_0_0_var(--ink)] group-hover:block ${place}`}
              >
                <span className="block text-xs font-medium leading-none">{word}</span>
                <span className="mt-1 block font-mono text-[10px] leading-none text-slate">risk {risk.toFixed(2)}</span>
                {point.scanId ? (
                  <span className="mt-1 block font-mono text-[10px] leading-none text-slate">{point.scanId}</span>
                ) : null}
              </span>
              <span className={`block w-full ${COLOR[decision] || "bg-uv"}`} style={{ height: `${height}px` }} />
            </span>
          );
        })
      ) : (
        <span className="text-xs text-slate">No scans in this window yet</span>
      )}
    </div>
  );
}
