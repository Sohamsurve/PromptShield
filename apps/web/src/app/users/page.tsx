"use client";

import { useEffect, useState } from "react";
import { DECISION_LABEL, type Decision } from "@promptshield/shared-types";
import { fetchAccounts } from "@/lib/api";

type AccountRow = {
  email: string;
  name: string;
  prefix: string;
  created_at: number;
  keys_active: number;
  keys_total: number;
  scans: number;
  last_scan_at: number | null;
  decisions: Partial<Record<Decision, number>>;
};

const ORDER: Decision[] = ["allow", "sanitize", "quarantine", "block", "escalate"];

function when(stamp: number | null) {
  if (!stamp) return "—";
  return new Date(stamp * 1000).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function usage(decisions: AccountRow["decisions"]) {
  const parts = ORDER.filter((key) => (decisions[key] ?? 0) > 0).map(
    (key) => `${DECISION_LABEL[key]} ${decisions[key]}`,
  );
  return parts.length ? parts.join(" · ") : "—";
}

export default function UsersPage() {
  const [items, setItems] = useState<AccountRow[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    fetchAccounts()
      .then((body) => setItems(Array.isArray(body?.items) ? body.items : []))
      .catch((e) => setError(String(e)))
      .finally(() => setReady(true));
  }, []);

  const scans = items.reduce((sum, row) => sum + row.scans, 0);

  return (
    <div className="min-w-0 space-y-4 p-4 md:p-6" data-testid="users-page">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight">Users</h1>
        <p className="text-sm text-slate">
          Signed-in accounts, their keys, and the scans stored on each account.
        </p>
      </header>
      {error ? <p className="text-sm text-block">{error}</p> : null}
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-panel border border-rule bg-surface px-4 py-3">
          <p className="text-xs text-slate">Accounts</p>
          <p className="font-mono text-2xl">{ready ? items.length : "—"}</p>
        </div>
        <div className="rounded-panel border border-rule bg-surface px-4 py-3">
          <p className="text-xs text-slate">Account scans</p>
          <p className="font-mono text-2xl">{ready ? scans : "—"}</p>
        </div>
        <div className="rounded-panel border border-rule bg-surface px-4 py-3">
          <p className="text-xs text-slate">Active keys</p>
          <p className="font-mono text-2xl">{ready ? items.reduce((sum, row) => sum + row.keys_active, 0) : "—"}</p>
        </div>
      </div>
      <div className="overflow-auto rounded-panel border border-rule bg-surface">
        <table className="w-full text-sm">
          <thead className="border-b border-rule text-left text-xs text-slate">
            <tr>
              <th className="px-3 py-2 font-medium">Name</th>
              <th className="px-3 py-2 font-medium">Email</th>
              <th className="px-3 py-2 font-medium">Keys</th>
              <th className="px-3 py-2 font-medium">Scans</th>
              <th className="px-3 py-2 font-medium">Usage</th>
              <th className="px-3 py-2 font-medium">Last scan</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr key={row.email} className="border-b border-rule last:border-0">
                <td className="px-3 py-2">
                  <p>{row.name}</p>
                  <p className="font-mono text-xs text-slate">{row.prefix ? `${row.prefix}…` : "—"}</p>
                </td>
                <td className="whitespace-nowrap px-3 py-2">{row.email}</td>
                <td className="whitespace-nowrap px-3 py-2 font-mono text-xs">
                  {row.keys_active}
                  {row.keys_total !== row.keys_active ? ` active of ${row.keys_total}` : ""}
                </td>
                <td className="whitespace-nowrap px-3 py-2 font-mono text-xs">{row.scans}</td>
                <td className="px-3 py-2 text-xs text-slate">{usage(row.decisions)}</td>
                <td className="whitespace-nowrap px-3 py-2 text-xs text-slate">{when(row.last_scan_at)}</td>
              </tr>
            ))}
            {ready && items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-3 py-8 text-sm text-slate">
                  No accounts yet. A caller appears here after they create an account.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
