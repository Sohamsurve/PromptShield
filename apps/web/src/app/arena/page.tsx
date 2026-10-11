"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ArenaLane, type ArenaResult } from "@/components/arena-lane";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldContent, FieldDescription, FieldLabel } from "@/components/ui/field";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiBase, fetchFixtures, runDemo } from "@/lib/api";
import { sitePaths } from "@/lib/site-paths";

type FixtureMeta = { id: string; title: string; label?: string };

const STEPS = [
  {
    title: "Pick a known attack",
    body: "Each fixture is a saved example, such as a hidden instruction in an email. You are not uploading your own file here.",
  },
  {
    title: "Run both sides",
    body: "The same example is given to an unprotected agent and to an agent with PromptShield in front of it.",
  },
  {
    title: "Read the outcome",
    body: "Harmed means the agent did what the attack asked. Safe means it finished the real task without doing that.",
  },
];

export default function ArenaPage() {
  const paths = sitePaths(usePathname() || "/arena");
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
  const options = fixtures.length ? fixtures : [{ id: "F01", title: "F01" }];
  const toolDenyNote = useMemo(() => {
    const denied = (on?.tool_logs ?? []).filter((t) => t.denied);
    if (!textScanning && denied.length) {
      return `Tool call denied — ${denied[0].reason ?? "tainted arg"}`;
    }
    return null;
  }, [on, textScanning]);

  let lesson: string | null = null;
  if (off && on) {
    if (off.outcome.harmed && !on.outcome.harmed) {
      lesson = "The unprotected agent followed the attack. PromptShield stopped it.";
    } else if (!off.outcome.harmed && !on.outcome.harmed) {
      lesson = "Neither agent was harmed on this example.";
    } else if (off.outcome.harmed && on.outcome.harmed) {
      lesson = "Both agents were harmed. Open X-ray on the protected side to see what got through.";
    } else {
      lesson = "The unprotected agent stayed safe and the protected agent was harmed. Read both lanes before drawing a conclusion.";
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-5 p-4 md:p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex max-w-2xl flex-col gap-1">
          <h1 className="text-2xl font-bold tracking-tight">A/B Arena</h1>
          <p className="text-sm text-slate">
            Watch one attack hit two agents. The left side has no firewall. The right side is protected by PromptShield.
            Gallery fixtures are in-sample, not an independent test.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
          <div className="min-w-56">
            <Select value={fixtureId} onValueChange={setFixtureId}>
              <SelectTrigger aria-label="Fixture">
                <SelectValue placeholder="Choose a fixture" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {options.map((f) => (
                    <SelectItem key={f.id} value={f.id}>
                      {f.id} · {f.title}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
          <Button type="button" onClick={onRun} disabled={loading}>
            {loading ? "Running…" : "Run both"}
          </Button>
          <Button type="button" variant="outline" onClick={onRunAll} disabled={loading}>
            Run all fixtures
          </Button>
          <Badge variant="secondary">
            Scoreboard: {scoreNeutralised}/{scoreTotal || "—"} neutralised
          </Badge>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {STEPS.map((step) => (
          <Card key={step.title}>
            <CardHeader className="p-4">
              <CardTitle className="text-base">{step.title}</CardTitle>
              <CardDescription>{step.body}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>

      {error ? (
        <Alert>
          <AlertTitle>The run did not finish</AlertTitle>
          <AlertDescription>
            {error}. Is the API running at {apiBase()}?
          </AlertDescription>
        </Alert>
      ) : null}

      {lesson ? (
        <Alert>
          <AlertTitle>What this run shows</AlertTitle>
          <AlertDescription>{lesson}</AlertDescription>
        </Alert>
      ) : null}

      <div className="hidden gap-3 md:grid md:grid-cols-2">
        <ArenaLane title="Unprotected agent" result={off} />
        <ArenaLane title="Protected by PromptShield" result={on} />
      </div>

      <Tabs defaultValue="off" className="md:hidden">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="off">Unprotected</TabsTrigger>
          <TabsTrigger value="on">Protected</TabsTrigger>
        </TabsList>
        <TabsContent value="off">
          <ArenaLane title="Unprotected agent" result={off} />
        </TabsContent>
        <TabsContent value="on">
          <ArenaLane title="Protected by PromptShield" result={on} />
        </TabsContent>
      </Tabs>

      <Card>
        <CardContent className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between">
          <Field orientation="horizontal">
            <FieldContent>
              <FieldLabel htmlFor="disable-text-scan">Disable text scanning (prove the tool firewall)</FieldLabel>
              <FieldDescription>
                {toolDenyNote ??
                  (textScanning
                    ? "Layers 1–4 and the tool firewall are on. The document is scanned before the agent acts."
                    : "Text detectors are off. The tool firewall still refuses a dangerous tool call.")}
              </FieldDescription>
            </FieldContent>
            <Switch
              id="disable-text-scan"
              checked={!textScanning}
              onCheckedChange={(checked) => setTextScanning(!checked)}
              aria-label="Disable text scanning (prove the tool firewall)"
            />
          </Field>
        </CardContent>
      </Card>

      <p className="text-sm text-slate">
        Neutralised on the scoreboard means the unprotected agent was harmed and the protected agent was not. To paste
        your own prompt or drop a file, use{" "}
        <Link href={paths.redteam} className="text-uv underline-offset-2 hover:underline">
          Red team
        </Link>{" "}
        or{" "}
        <Link href={paths.scans} className="text-uv underline-offset-2 hover:underline">
          Scans
        </Link>
        .
      </p>
    </div>
  );
}
