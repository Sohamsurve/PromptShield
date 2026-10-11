"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { createMyKey, fetchMyKeys, revokeMyKey, storedBearer } from "@/lib/api";

type KeyRow = {
  key_id: string;
  name: string;
  prefix: string;
  created_at: number;
  revoked: boolean;
  primary?: boolean;
};

export default function UserKeysPage() {
  const [rows, setRows] = useState<KeyRow[]>([]);
  const [name, setName] = useState("");
  const [fresh, setFresh] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [ready, setReady] = useState(false);
  const [signedIn, setSignedIn] = useState(false);

  async function load() {
    if (!storedBearer()) {
      setSignedIn(false);
      setReady(true);
      return;
    }
    setSignedIn(true);
    const body = await fetchMyKeys();
    setRows(body.items);
    setReady(true);
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
      const created = await createMyKey(label);
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
      await revokeMyKey(keyId);
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

  if (!ready && !error) {
    return <p className="p-6 text-sm text-slate">Loading keys…</p>;
  }

  if (!signedIn && !error) {
    return (
      <div className="space-y-3 p-4 md:p-6">
        <h1 className="text-2xl font-bold tracking-tight">API keys</h1>
        <p className="text-sm text-slate">
          <Link href="/login" className="text-uv hover:underline">
            Sign in
          </Link>{" "}
          to manage keys for your account.
        </p>
      </div>
    );
  }

  return (
    <div className="min-w-0 max-w-3xl space-y-4 p-4 md:p-6">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">API keys</h1>
        <p className="text-sm text-slate">
          Create a key for an app. The secret is shown once. Scans from every key on this account stay in your list.
          The key from sign-up stays.
        </p>
      </header>
      {error ? <p className="text-sm text-block">{error}</p> : null}
      <form onSubmit={onCreate} className="flex flex-wrap items-end gap-2 rounded-panel border border-rule bg-surface p-4">
        <div className="min-w-[12rem] flex-1">
          <label htmlFor="key-name" className="mb-1.5 block text-sm font-medium leading-none">
            Name
          </label>
          <input
            id="key-name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Laptop"
            className="w-full rounded-panel border border-rule bg-background px-3 text-sm"
          />
        </div>
        <Button type="submit" disabled={pending}>
          {pending ? "Creating" : "Create key"}
        </Button>
      </form>
      {fresh ? (
        <div className="space-y-2 rounded-panel border border-rule bg-surface p-4">
          <p className="text-sm font-medium">Copy this key now. It is not shown again.</p>
          <pre className="overflow-x-auto rounded-panel border border-rule bg-background p-3 text-xs">{fresh}</pre>
          <Button type="button" variant="outline" onClick={copyFresh}>
            Copy
          </Button>
        </div>
      ) : null}
      <ul className="space-y-2">
        {rows.map((row) => (
          <li key={row.key_id} className="flex flex-wrap items-center justify-between gap-2 rounded-panel border border-rule bg-surface px-3 py-2">
            <div>
              <p className="text-sm font-medium">{row.name}</p>
              <p className="font-mono text-xs text-slate">
                {row.prefix}… {row.revoked ? "· Revoked" : "· Active"}
                {row.primary ? " · Account key" : ""}
              </p>
            </div>
            {row.revoked || row.primary ? null : (
              <Button type="button" variant="outline" size="sm" onClick={() => onRevoke(row.key_id)}>
                Revoke
              </Button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
