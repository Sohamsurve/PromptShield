"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FileDrop } from "@/components/file-drop";
import { Button } from "@/components/ui/button";
import { VerdictBadge } from "@/components/verdict-badge";
import { fetchScans, postScan, postScanFile, storedBearer } from "@/lib/api";
import type { Decision } from "@promptshield/shared-types";

type ScanRow = {
  scan_id: string;
  decision: Decision;
  risk: number;
  attack_types?: string[];
  safe_alternative?: string | null;
};

export default function UserScansPage() {
  const [items, setItems] = useState<ScanRow[]>([]);
  const [paste, setPaste] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [signedIn, setSignedIn] = useState(false);
  const router = useRouter();

  const reload = useCallback(() => {
    if (!storedBearer()) {
      setSignedIn(false);
      setReady(true);
      return;
    }
    setSignedIn(true);
    fetchScans(100)
      .then((body) => setItems(Array.isArray(body?.items) ? body.items : []))
      .catch((e) => setError(String(e)))
      .finally(() => setReady(true));
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const content = paste.trim();
    if (!content) return;
    setBusy(true);
    setError(null);
    try {
      const result = await postScan(content, "user_message");
      setPaste("");
      if (result?.scan_id) {
        router.push(`/portal/scans/${result.scan_id}`);
        return;
      }
      reload();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function onFile(file: File) {
    setBusy(true);
    setError(null);
    try {
      const result = await postScanFile(file);
      if (result?.scan_id) {
        router.push(`/portal/scans/${result.scan_id}`);
        return;
      }
      reload();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  if (!ready) {
    return <p className="p-6 text-sm text-slate">Loading scans…</p>;
  }

  if (!signedIn) {
    return (
      <div className="space-y-3 p-4 md:p-6">
        <h1 className="text-2xl font-bold tracking-tight">Scans</h1>
        <p className="text-sm text-slate">
          <Link href="/login" className="text-uv hover:underline">
            Sign in
          </Link>{" "}
          to see the scans on your account.
        </p>
      </div>
    );
  }

  return (
    <div className="min-w-0 space-y-4 p-4 md:p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Scans</h1>
        <p className="text-sm text-slate">
          Paste a prompt or drop a file. The check uses your signed-in key and stays on this account.
        </p>
      </header>
      {error ? <p className="text-sm text-block">{error}</p> : null}
      <form onSubmit={onSubmit} className="space-y-3 rounded-panel border border-rule bg-surface p-4">
        <label htmlFor="prompt" className="text-sm font-medium">
          Check a prompt
        </label>
        <textarea
          id="prompt"
          value={paste}
          onChange={(event) => setPaste(event.target.value)}
          rows={4}
          placeholder="Paste a prompt…"
          disabled={busy}
          className="w-full rounded-panel border border-rule bg-background px-3 py-2 text-sm"
        />
        <FileDrop disabled={busy} onFile={onFile} label="Drop a file here, or click to choose" />
        <Button type="submit" disabled={busy || !paste.trim()}>
          {busy ? "Checking" : "Check"}
        </Button>
      </form>
      <div className="overflow-auto rounded-panel border border-rule bg-surface">
        <table className="w-full text-sm">
          <thead className="border-b border-rule text-left text-xs text-slate">
            <tr>
              <th className="px-3 py-2 font-medium">Verdict</th>
              <th className="px-3 py-2 font-medium">Risk</th>
              <th className="px-3 py-2 font-medium">Types</th>
              <th className="px-3 py-2 font-medium">Scan</th>
            </tr>
          </thead>
          <tbody>
            {items.map((scan) => (
              <tr key={scan.scan_id} className="border-b border-rule last:border-0">
                <td className="px-3 py-2">
                  <VerdictBadge decision={scan.decision} />
                </td>
                <td className="px-3 py-2 font-mono text-xs">{Number(scan.risk).toFixed(2)}</td>
                <td className="px-3 py-2 text-xs text-slate">{(scan.attack_types ?? []).slice(0, 2).join(", ") || "—"}</td>
                <td className="px-3 py-2">
                  <Link href={`/portal/scans/${scan.scan_id}`} className="font-mono text-xs text-uv hover:underline">
                    {scan.scan_id}
                  </Link>
                </td>
              </tr>
            ))}
            {items.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-3 py-8 text-sm text-slate">
                  No scans for this account yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
