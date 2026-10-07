"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArenaLane, type ArenaResult } from "@/components/arena-lane";
import { apiBase, fetchFixtures, runDemo } from "@/lib/api";

type FixtureMeta = { id: string; title: string; label?: string };

export default function ArenaPage() {
  const [fixtures, setFixtures] = useState<FixtureMeta[]>([]);
  const [fixtureId, setFixtureId] = useState("F01");
  const [results, setResults] = useState<ArenaResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [textScanning, setTextScanning] = useState(true);
  const [scoreNeutralised, setScoreNeutralised] = useState(0);
  const [scoreTotal, setScoreTotal] = useState(0);

  useEffect(() => {
    fetchFixtures()
      .then((data: FixtureMeta[]) => setFixtures(data))
      .catch((e) => setError(String(e)));
  }, []);

  async function onRun() {
    setLoading(true);
    setError(null);
    try {
      const data = await runDemo(fixtureId, ["off", "on"], { textScanning });
      setResults(data.results);
      const off = data.results.find((r: ArenaResult) => r.lane === "off");
      const on = data.results.find((r: ArenaResult) => r.lane === "on");
      if (off?.outcome.harmed && on && !on.outcome.harmed) {
        setScoreNeutralised((n) => n + 1);
      }
      setScoreTotal((n) => n + 1);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function onRunAll() {
    setLoading(true);
    setError(null);
    const attacks = (fixtures.length ? fixtures : []).filter((f) => f.label === "attack" || f.id.startsWith("F"));
    const list = attacks.length ? attacks.filter((f) => !["F18", "F19", "F20"].includes(f.id)) : [{ id: "F01", title: "F01" }];
    let neut = 0;
    let total = 0;
    try {
      for (const f of list.slice(0, 12)) {
        const data = await runDemo(f.id, ["off", "on"], { textScanning: true });
        const off = data.results.find((r: ArenaResult) => r.lane === "off");
        const on = data.results.find((r: ArenaResult) => r.lane === "on");
        total += 1;
        if (off?.outcome.harmed && on && !on.outcome.harmed) neut += 1;
        if (f.id === fixtureId) setResults(data.results);
      }
      setScoreNeutralised(neut);
      setScoreTotal(total);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  const off = results?.find((r) => r.lane === "off");
  const on = results?.find((r) => r.lane === "on");
  const toolDenyNote = useMemo(() => {
    const denied = (on?.tool_logs ?? []).filter((t) => t.denied);
    if (!textScanning && denied.length) {
      return `Tool call denied — ${denied[0].reason ?? "tainted arg"}`;
    }
    return null;
  }, [on, textScanning]);

  return (
    <div className="p-4 md:p-6 space-y-4">
      <div className="flex flex-col lg:flex-row lg:items-end gap-3 justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">A/B Arena</h1>
          <p className="text-slate text-sm mt-1 max-w-prose">
            Same gallery attack, unprotected vs protected agent. Fixtures F01–F20 only — no free-text
            upload here. To paste a prompt or drop a file, use{" "}
            <Link href="/redteam" className="text-uv underline">
              Red team
            </Link>{" "}
            or{" "}
            <Link href="/scans" className="text-uv underline">
              Scans
            </Link>
            . Gallery fixtures are <span className="font-mono">in-sample</span> (not independent sealed).
          </p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <label className="text-sm text-slate">
            Fixture{" "}
            <select
              className="ml-1 border border-rule rounded-panel bg-surface px-2 py-1.5 text-ink"
              value={fixtureId}
              onChange={(e) => setFixtureId(e.target.value)}
            >
              {(fixtures.length ? fixtures : [{ id: "F01", title: "F01" }]).map((f) => (
                <option key={f.id} value={f.id}>
                  {f.id} · {f.title}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            onClick={onRun}
            disabled={loading}
            className="rounded-panel bg-ink text-paper px-3 py-1.5 text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Running…" : "Run both"}
          </button>
          <button
            type="button"
            onClick={onRunAll}
            disabled={loading}
            className="rounded-panel border border-rule bg-surface px-3 py-1.5 text-sm font-medium disabled:opacity-50"
          >
            Run all fixtures
          </button>
          <div className="text-sm text-slate font-mono">
            Scoreboard: {scoreNeutralised}/{scoreTotal || "—"} neutralised
          </div>
        </div>
      </div>

      {error ? (
        <p className="text-sm text-block">
          {error}. Is the API running at {apiBase()}?
        </p>
      ) : null}

      <div className="grid md:grid-cols-2 gap-3">
        <ArenaLane title="Unprotected agent" result={off} />
        <ArenaLane title="Protected by PromptShield" result={on} />
      </div>

      <div className="rounded-panel border border-rule bg-surface p-3 flex flex-col sm:flex-row sm:items-center gap-3 justify-between">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={!textScanning}
            onChange={(e) => setTextScanning(!e.target.checked)}
            className="accent-[var(--uv)]"
          />
          Disable text scanning (prove the tool firewall)
        </label>
        <p className="text-sm text-slate">
          {toolDenyNote ??
            (textScanning
              ? "Layers 1–4 + tool firewall active."
              : "Text detectors off; tool firewall still on.")}
        </p>
      </div>
    </div>
  );
}
