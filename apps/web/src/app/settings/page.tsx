"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldDescription, FieldLabel, FieldTitle } from "@/components/ui/field";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { apiBase, applyPolicyPreset, fetchHealthz, fetchPolicy } from "@/lib/api";

const MORE_LINKS = [
  { href: "/scans", label: "Scans", detail: "Paste text or drop a file and read the verdict." },
  { href: "/policy", label: "Policy", detail: "Fine-tune thresholds, rules, and tool limits." },
  { href: "/redteam", label: "Red team", detail: "Try your own wording against the firewall." },
  { href: "/eval", label: "Eval", detail: "See measured recall, false alarms, and latency." },
  { href: "/integrate", label: "Integrate", detail: "Call the firewall from another agent with an API key." },
  { href: "/keys", label: "Keys", detail: "Create a bearer key for a caller. The secret is shown once." },
  { href: "/users", label: "Users", detail: "See each account, its keys, and how many scans it has run." },
];

type PresetName = "balanced" | "low_false_alarms";

type Health = {
  status?: string;
  judge_mode?: string;
  judge_model?: string;
  llm_provider?: string;
  api_key_configured?: boolean;
  judge_timeout_ms?: number;
  judge_reasoning_effort?: string;
};

type PresetInfo = { label?: string; dev_acted?: number; dev_fpr?: number; note?: string };

function pct(n?: number) {
  if (n == null || Number.isNaN(n)) return "—";
  const value = n * 100;
  return `${value < 10 ? value.toFixed(1) : value.toFixed(0)}%`;
}

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [preset, setPreset] = useState<PresetName | "custom" | "unknown">("unknown");
  const [presets, setPresets] = useState<Record<string, PresetInfo>>({});
  const [version, setVersion] = useState("—");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setMounted(true), []);

  function readPolicy(p: Record<string, unknown>) {
    const meta = (p._meta ?? {}) as {
      presets?: Record<string, PresetInfo>;
      active_version?: number;
    };
    setPresets(meta.presets ?? {});
    setVersion(String(p.version ?? meta.active_version ?? "—"));
    const note = String(p.operating_point_note ?? "").toLowerCase();
    const differs = Boolean((p._meta as { differs_from_template?: boolean } | undefined)?.differs_from_template);
    if (note.includes("low false")) setPreset("low_false_alarms");
    else if (differs) setPreset("custom");
    else setPreset("balanced");
  }

  useEffect(() => {
    fetchHealthz()
      .then((body) => {
        setHealth(body);
        setHealthError(null);
      })
      .catch((e) => setHealthError(String(e)));
    fetchPolicy()
      .then(readPolicy)
      .catch((e) => setError(String(e)));
  }, []);

  async function onPreset(next: PresetName) {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await applyPolicyPreset(next);
      const fresh = await fetchPolicy();
      readPolicy(fresh);
      setNotice(next === "balanced" ? "Balanced preset saved." : "Low false alarms preset saved.");
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  const live = health?.judge_mode === "live";

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 p-4 md:p-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-slate">
          Choose the look of this console and how strict the firewall is. The judge model is set on the server.
        </p>
      </div>

      {healthError ? (
        <Alert>
          <AlertTitle>API not reachable</AlertTitle>
          <AlertDescription>
            Settings that talk to the firewall need the API. Start it, then refresh. Theme still saves in this browser.
          </AlertDescription>
        </Alert>
      ) : null}
      {error ? (
        <Alert>
          <AlertTitle>Could not update the firewall</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}
      {notice ? (
        <Alert>
          <AlertTitle>Saved</AlertTitle>
          <AlertDescription>{notice} New scans use this setting. Open Policy to adjust individual thresholds.</AlertDescription>
        </Alert>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Saved in this browser. System follows the device.</CardDescription>
        </CardHeader>
        <CardContent>
          <Field>
            <FieldLabel>Theme</FieldLabel>
            <div className="h-10">
              {mounted ? (
                <ToggleGroup
                  type="single"
                  variant="outline"
                  className="justify-start"
                  value={theme}
                  onValueChange={(value) => {
                    if (value === "light" || value === "dark" || value === "system") setTheme(value);
                  }}
                  aria-label="Theme"
                >
                  <ToggleGroupItem value="light">Light</ToggleGroupItem>
                  <ToggleGroupItem value="dark">Dark</ToggleGroupItem>
                  <ToggleGroupItem value="system">System</ToggleGroupItem>
                </ToggleGroup>
              ) : null}
            </div>
          </Field>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Firewall sensitivity</CardTitle>
          <CardDescription>
            This changes every new scan, including Arena, Scans, and Red team. Policy version {version}.
            {preset === "custom" ? " Current thresholds are custom." : ""}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid gap-3 md:grid-cols-2">
            <button
              type="button"
              disabled={busy}
              onClick={() => onPreset("balanced")}
              className={`rounded-panel border p-4 text-left ${
                preset === "balanced" ? "border-uv bg-accent" : "border-border bg-card"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <FieldTitle>Balanced</FieldTitle>
                {preset === "balanced" ? <Badge variant="secondary">In use</Badge> : null}
              </div>
              <p className="mt-2 text-sm text-slate">
                Catches more attacks and also flags more ordinary text. Development set: acted on{" "}
                {pct(presets.balanced?.dev_acted ?? 0.575)} of attacks, false alarms{" "}
                {pct(presets.balanced?.dev_fpr ?? 0.106)}.
              </p>
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={() => onPreset("low_false_alarms")}
              className={`rounded-panel border p-4 text-left ${
                preset === "low_false_alarms" ? "border-uv bg-accent" : "border-border bg-card"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <FieldTitle>Low false alarms</FieldTitle>
                {preset === "low_false_alarms" ? <Badge variant="secondary">In use</Badge> : null}
              </div>
              <p className="mt-2 text-sm text-slate">
                Stays quieter. More attacks get through. Development set: acted on{" "}
                {pct(presets.low_false_alarms?.dev_acted ?? 0.25)} of attacks, false alarms{" "}
                {pct(presets.low_false_alarms?.dev_fpr ?? 0.0156)}.
              </p>
            </button>
          </div>
          <p className="text-xs text-slate">
            Those rates are development measurements, not a guarantee.{" "}
            <Link href="/policy" className="text-uv underline-offset-2 hover:underline">
              Open Policy
            </Link>{" "}
            for per-source thresholds.
          </p>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Judge</CardTitle>
            <CardDescription>
              A language model reviews uncertain text. It never decides alone. Signatures and the classifier still run.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="text-slate">Status</span>
              <Badge variant="outline">{live ? "Live" : health ? "Offline" : "Unknown"}</Badge>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-slate">Model</span>
              <span className="font-mono text-xs">{health?.judge_model || "—"}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-slate">Provider</span>
              <span className="font-mono text-xs">{health?.llm_provider || "—"}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-slate">Reasoning</span>
              <span className="font-mono text-xs">{health?.judge_reasoning_effort || "—"}</span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-slate">Timeout</span>
              <span className="font-mono text-xs">
                {health?.judge_timeout_ms != null ? `${health.judge_timeout_ms} ms` : "—"}
              </span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-slate">API key</span>
              <span>{health?.api_key_configured ? "Configured" : "Not configured"}</span>
            </div>
            <FieldDescription>
              Change the model with LLM_MODEL_JUDGE in the server environment, then restart the API. This screen does not store the key.
            </FieldDescription>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Demo agent</CardTitle>
            <CardDescription>Used by the Arena so the comparison is repeatable.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="text-slate">Mode</span>
              <span className="font-mono text-xs">ARIA_MODE=scripted</span>
            </div>
            <FieldDescription>
              The demo agent follows instructions on purpose. It uses mock tools and canary values only, so you can see harm without sending real email or reading real files.
            </FieldDescription>
            <Button variant="outline" asChild>
              <Link href="/arena">Open the Arena</Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Connection</CardTitle>
          <CardDescription>The browser talks to the API through this app.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2 text-sm">
          <div className="font-mono text-xs break-all">{apiBase()}</div>
          <FieldDescription>
            Set NEXT_PUBLIC_API_BASE for server-side calls. In the browser, requests go to /api/v1 and this app proxies them.
          </FieldDescription>
        </CardContent>
      </Card>

      <Card className="md:hidden">
        <CardHeader>
          <CardTitle>More screens</CardTitle>
          <CardDescription>These stay in the side menu on a wide screen.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {MORE_LINKS.map((item) => (
            <Link key={item.href} href={item.href} className="flex flex-col gap-0.5">
              <span className="text-sm font-medium text-uv">{item.label}</span>
              <span className="text-xs text-slate">{item.detail}</span>
            </Link>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
