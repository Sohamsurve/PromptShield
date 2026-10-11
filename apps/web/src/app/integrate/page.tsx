"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchHealthz } from "@/lib/api";

const SNIPPETS: { id: string; title: string; detail: string; code: string }[] = [
  {
    id: "scan",
    title: "Check a prompt",
    detail: "Call this before the model, from any app or agent. On sanitize, send sanitized_text onward. On block, stop.",
    code: `curl -s http://127.0.0.1:8000/v1/scan \\
  -H "authorization: Bearer $PROMPTSHIELD_API_KEY" \\
  -H "content-type: application/json" \\
  -d '{"source_type":"user_message","trust":1,"content":"Summarise the thread."}'`,
  },
  {
    id: "file",
    title: "Check a file",
    detail: "PDF, Office, HTML, email, image, and source files. The response uses the same decision and sanitized_text.",
    code: `curl -s http://127.0.0.1:8000/v1/scan/file \\
  -H "authorization: Bearer $PROMPTSHIELD_API_KEY" \\
  -F "file=@notes.txt"`,
  },
  {
    id: "tool",
    title: "Check a tool call",
    detail: "deny means the tool must not run. confirm means a person should approve it first.",
    code: `curl -s http://127.0.0.1:8000/v1/guard/tool-call \\
  -H "x-api-key: $PROMPTSHIELD_API_KEY" \\
  -H "content-type: application/json" \\
  -d '{"session_id":"s_42","tool":"send_email","args":{"to":"ops@example.test","body":"status"}}'`,
  },
];

type Health = {
  firewall_auth?: string;
  firewall_key_configured?: boolean;
};

export default function IntegratePage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    fetchHealthz()
      .then((body) => {
        setHealth(body);
        setHealthError(null);
      })
      .catch((e) => setHealthError(String(e)));
  }, []);

  async function copy(id: string, code: string) {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(id);
      return;
    } catch {
      const area = document.createElement("textarea");
      area.value = code;
      area.setAttribute("readonly", "true");
      document.body.appendChild(area);
      area.select();
      const ok = document.execCommand("copy");
      area.remove();
      setCopied(ok ? id : null);
    }
  }

  const demo = health?.firewall_auth !== "api_key";

  const steps = [
    {
      title: "Send the untrusted text",
      detail: "POST /v1/scan for a prompt. POST /v1/scan/file for an upload.",
    },
    {
      title: "Read the decision",
      detail: "Allowed, Sanitised, Quarantined, or Blocked. The field is decision.",
    },
    {
      title: "Forward only the safe text",
      detail: "On Sanitised, send sanitized_text to your model. On Blocked or Quarantined, do not send the original.",
    },
  ];

  return (
    <div className="mx-auto w-full max-w-5xl space-y-4 p-4 md:p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Integrate</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-slate">
          Any agent calls the same firewall before it calls its own model. OpenAI, LangGraph, NeMo, and a custom app
          all use these endpoints. PromptShield does not replace the model.
        </p>
      </header>

      <div className="grid items-stretch gap-4 md:grid-cols-3">
        {steps.map((step, index) => (
          <Card key={step.title} className="h-full">
            <CardHeader className="h-full gap-3">
              <p className="text-xs font-bold uppercase tracking-wide text-muted-foreground">Step {index + 1}</p>
              <CardTitle className="min-h-12 leading-snug">{step.title}</CardTitle>
              <CardDescription className="leading-relaxed">{step.detail}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Authentication</CardTitle>
          <CardDescription>
            The service key is PROMPTSHIELD_API_KEY on the API process. This screen never shows the key.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {healthError ? <p className="text-block">{healthError}</p> : null}
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{demo ? "Demo open" : "Key required"}</Badge>
            <span className="text-slate">
              {demo
                ? "This API is in demo mode, so local calls work without a key."
                : health?.firewall_key_configured
                  ? "Callers must send the service key."
                  : "Key mode is on, and no service key is configured. Set PROMPTSHIELD_API_KEY and restart the API."}
            </span>
          </div>
          <p>
            <Link href="/signup">Create an account</Link> to get an API key. The key is shown once. Send it as a bearer
            token. That account only sees its own scans. Admins can also create keys on the{" "}
            <Link href="/keys">Keys</Link> page.
          </p>
          <p>
            For a shared service, set <span className="font-mono text-xs">DEMO_MODE=0</span> and{" "}
            <span className="font-mono text-xs">PROMPTSHIELD_API_KEY</span>, then restart the API. Callers send either
            header:
          </p>
          <pre className="overflow-x-auto rounded-panel border-2 border-ink bg-background p-3 text-xs leading-relaxed">
            authorization: Bearer YOUR_KEY{"\n"}
            x-api-key: YOUR_KEY
          </pre>
          <p className="text-slate">
            Health and this dashboard stay readable without the key. Scan and guard calls require it when demo mode is
            off. A wrong key returns 401 and the key is never written back in the response.
          </p>
        </CardContent>
      </Card>

      {SNIPPETS.map((item) => (
        <Card key={item.id}>
          <CardHeader>
            <CardTitle>{item.title}</CardTitle>
            <CardDescription>{item.detail}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <pre className="overflow-x-auto rounded-panel border-2 border-ink bg-background p-3 text-xs leading-relaxed">{item.code}</pre>
            <Button type="button" variant="outline" size="sm" onClick={() => copy(item.id, item.code)}>
              {copied === item.id ? "Copied" : "Copy"}
            </Button>
          </CardContent>
        </Card>
      ))}

      <Card>
        <CardHeader>
          <CardTitle>What to do with the body</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <p>
            <span className="font-medium">Allowed.</span> Send the original text to your model.
          </p>
          <p>
            <span className="font-medium">Sanitised.</span> Send sanitized_text. The attack span has been replaced.
            spotlighted_text is the same text marked as untrusted data.
          </p>
          <p>
            <span className="font-medium">Blocked or Quarantined.</span> Do not send the original text to the model.
            Show <span className="font-mono text-xs">safe_alternative</span> instead. That line is the benign remainder, or a request to rephrase, and it does not repeat the attack.
          </p>
          <p className="text-slate">The same steps are written out in docs/INTEGRATIONS.md.</p>
        </CardContent>
      </Card>
    </div>
  );
}
