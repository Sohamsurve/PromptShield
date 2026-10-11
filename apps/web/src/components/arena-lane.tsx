import Link from "next/link";
import { usePathname } from "next/navigation";
import { VerdictBadge } from "@/components/verdict-badge";
import { OutcomeBanner } from "@/components/outcome-banner";
import { sitePaths } from "@/lib/site-paths";
import type { Decision } from "@promptshield/shared-types";

type Step = Record<string, unknown>;

export type ArenaResult = {
  lane?: string;
  scan?: {
    scan_id?: string;
    decision?: Decision;
    risk?: number;
    sanitized_text?: string | null;
  } | null;
  outcome: {
    harmed: boolean;
    task_completed: boolean;
    canary_leaked?: boolean;
    unauthorized_send?: boolean;
    unauthorized_read?: boolean;
    memory_poisoned?: boolean;
    role_hijacked?: boolean;
  };
  steps?: Step[];
  tool_logs?: Array<{ tool: string; denied?: boolean; reason?: string | null; args?: unknown }>;
};

export function ArenaLane({
  title,
  result,
}: {
  title: string;
  result?: ArenaResult | null;
}) {
  const paths = sitePaths(usePathname() || "/arena");
  const harmed = Boolean(result?.outcome.harmed);
  const decision = result?.scan?.decision;
  const deniedTools = (result?.tool_logs ?? []).filter((t) => t.denied);

  let detail = harmed ? "outcome flag fired" : "task completed";
  if (harmed && result?.outcome.unauthorized_send) detail = "unauthorized send";
  if (harmed && result?.outcome.canary_leaked) detail = "canary leaked";
  if (harmed && result?.outcome.role_hijacked) detail = "role hijacked";
  if (!harmed && deniedTools.length) detail = `tool call denied — ${deniedTools[0].reason ?? "tainted"}`;

  return (
    <section className="rounded-panel border border-rule bg-surface p-4 min-h-[260px] flex flex-col">
      <div className="flex items-start justify-between gap-2">
        <h2 className="font-medium">{title}</h2>
        {decision ? <VerdictBadge decision={decision} /> : null}
      </div>
      {result?.scan?.risk != null ? (
        <p className="text-xs text-slate mt-1 font-mono">risk {result.scan.risk.toFixed(2)}</p>
      ) : null}
      <ol className="mt-3 space-y-2 text-sm font-mono flex-1">
        {(result?.steps ?? []).slice(0, 8).map((step, i) => (
          <li key={i} className="border border-rule rounded-chip px-2 py-1.5 text-xs text-slate">
            <span className="text-ink">{String(step.stage ?? "step")}</span>
            {step.tool ? ` · ${String(step.tool)}` : ""}
            {step.denied ? " · denied" : ""}
            {step.detail ? `: ${String(step.detail).slice(0, 90)}` : ""}
          </li>
        ))}
        {!result ? (
          <li className="text-slate text-sm font-sans list-none">Run a fixture to see steps.</li>
        ) : null}
      </ol>
      {result ? <OutcomeBanner harmed={harmed} detail={detail} /> : null}
      {result?.scan?.scan_id ? (
        <Link
          href={paths.xray(result.scan.scan_id)}
          className="mt-3 text-sm text-uv underline-offset-2 hover:underline self-start"
        >
          Open X-ray
        </Link>
      ) : null}
    </section>
  );
}
