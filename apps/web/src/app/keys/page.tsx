"use client";

import { FormEvent, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { createKey, fetchKeys, revokeKey } from "@/lib/api";

type KeyRow = {
  key_id: string;
  name: string;
  prefix: string;
  role: string;
  created_at: number;
  revoked: boolean;
};

export default function KeysPage() {
  const [rows, setRows] = useState<KeyRow[]>([]);
  const [name, setName] = useState("");
  const [role, setRole] = useState<"user" | "admin">("user");
  const [fresh, setFresh] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function load() {
    const body = await fetchKeys();
    setRows(body.items);
  }

  useEffect(() => {
    load().catch((e) => setError(String(e)));
  }, []);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    const label = name.trim();
    if (!label) return;
    setPending(true);
    setError(null);
    try {
      const created = await createKey(label, role);
      setFresh(created.token);
      setName("");
      await load();
    } catch (e) {
      setError(String(e));
    } finally {
      setPending(false);
    }
  }

  async function onRevoke(keyId: string) {
    setError(null);
    try {
      await revokeKey(keyId);
      if (fresh) setFresh(null);
      await load();
    } catch (e) {
      setError(String(e));
    }
  }

  async function copyFresh() {
    if (!fresh) return;
    try {
      await navigator.clipboard.writeText(fresh);
    } catch {
      const area = document.createElement("textarea");
      area.value = fresh;
      area.setAttribute("readonly", "true");
      document.body.appendChild(area);
      area.select();
      document.execCommand("copy");
      area.remove();
    }
  }

  return (
    <div className="min-w-0 max-w-3xl space-y-4 p-4 md:p-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">Keys</h1>
        <p className="text-sm text-slate">
          The built-in admin sign-in stays fixed. A caller key sees only its own scans. An admin key opens admin control.
          The secret is shown once and is stored as a hash.
        </p>
      </header>

      <Card>
        <CardHeader>
          <CardTitle>New key</CardTitle>
          <CardDescription>Caller keys are for apps and people. Admin keys can open admin control.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-3 sm:flex-row sm:items-end" onSubmit={onCreate}>
            <label className="block flex-1 text-sm" htmlFor="key-name">
              Name
              <input
                id="key-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                className="mt-1 w-full rounded-panel border border-border bg-paper px-3 py-2 text-sm"
              />
            </label>
            <label className="block text-sm" htmlFor="key-role">
              Role
              <select
                id="key-role"
                value={role}
                onChange={(event) => setRole(event.target.value === "admin" ? "admin" : "user")}
                className="mt-1 w-full rounded-panel border border-border bg-paper px-3 py-2 text-sm"
              >
                <option value="user">Caller</option>
                <option value="admin">Admin</option>
              </select>
            </label>
            <Button type="submit" disabled={pending}>
              {pending ? "Creating" : "Create bearer key"}
            </Button>
          </form>
          {fresh ? (
            <div className="mt-4 space-y-2 rounded-panel border border-border bg-paper p-3">
              <p className="text-sm">Copy this key now. It will not be shown again.</p>
              <p className="break-all font-mono text-xs">{fresh}</p>
              <div className="flex gap-2">
                <Button type="button" variant="outline" size="sm" onClick={copyFresh}>
                  Copy
                </Button>
                <Button type="button" variant="outline" size="sm" onClick={() => setFresh(null)}>
                  I have saved this key
                </Button>
              </div>
            </div>
          ) : null}
          {error ? <p className="mt-3 text-sm text-block">{error}</p> : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Caller keys</CardTitle>
          <CardDescription>Revoking a key stops it immediately. Existing scans stay in your admin list.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {rows.length === 0 ? <p className="text-sm text-slate">No caller keys yet.</p> : null}
          {rows.map((row) => (
            <div key={row.key_id} className="flex flex-wrap items-center justify-between gap-2 border-b border-rule py-2">
              <div className="min-w-0">
                <p className="text-sm">{row.name}</p>
                <p className="font-mono text-xs text-slate">
                  {row.prefix}… · {row.role === "admin" ? "Admin" : "Caller"} · {row.revoked ? "Revoked" : "Active"}
                </p>
              </div>
              {row.revoked ? null : (
                <Button type="button" variant="outline" size="sm" onClick={() => onRevoke(row.key_id)}>
                  Revoke
                </Button>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
