import { Check, X } from "lucide-react";

export function MetricCard({
  label,
  measured,
  target,
  pass,
  format = (n: number) => n.toFixed(2),
  metLabel = false,
}: {
  label: string;
  measured: number | null;
  target: string;
  pass: boolean | null;
  format?: (n: number) => string;
  metLabel?: boolean;
}) {
  return (
    <div className="rounded-panel border border-rule bg-surface p-4">
      <div className="text-xs text-slate">{label}</div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="text-xl font-medium font-mono">
          {measured == null ? "—" : format(measured)}
        </span>
        <span className="text-xs text-slate">target {target}</span>
      </div>
      {pass == null ? null : (
        <div className={`mt-2 flex items-center gap-1.5 text-sm ${pass ? "text-allow" : "text-block"}`}>
          {pass ? <Check size={16} strokeWidth={1.5} aria-hidden /> : <X size={16} strokeWidth={1.5} aria-hidden />}
          <span>{metLabel ? (pass ? "MET" : "NOT MET") : pass ? "Pass" : "Fail"}</span>
        </div>
      )}
    </div>
  );
}
