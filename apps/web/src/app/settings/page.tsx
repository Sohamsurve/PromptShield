"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { apiBase } from "@/lib/api";

const MORE_LINKS = [
  { href: "/scans", label: "Scans" },
  { href: "/policy", label: "Policy" },
  { href: "/redteam", label: "Red team" },
  { href: "/eval", label: "Eval" },
];

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  return (
    <div className="p-4 md:p-6 space-y-4 max-w-xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-slate text-sm mt-1">Theme, API base, demo mode, and more screens.</p>
      </div>
      <section className="rounded-panel border border-rule bg-surface p-4 space-y-3">
        <div className="text-sm">
          <div className="text-slate text-xs">API base</div>
          <div className="font-mono text-sm mt-1 break-all">{mounted ? apiBase() : "—"}</div>
          <p className="text-xs text-slate mt-1">Set via NEXT_PUBLIC_API_BASE.</p>
        </div>
        <div className="text-sm">
          <div className="text-slate text-xs">Theme</div>
          <div className="mt-2 flex flex-wrap gap-2" role="group" aria-label="Theme">
            {(["light", "dark", "system"] as const).map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTheme(t)}
                className={`rounded-panel border px-3 py-1.5 text-sm capitalize ${
                  mounted && theme === t ? "border-uv text-uv" : "border-rule"
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
        <div className="text-sm">
          <div className="text-slate text-xs">Demo mode</div>
          <div className="font-mono mt-1">ARIA_MODE=scripted (API)</div>
        </div>
      </section>
      <section className="rounded-panel border border-rule bg-surface p-4 md:hidden">
        <h2 className="text-sm font-medium mb-2">More screens</h2>
        <ul className="space-y-2">
          {MORE_LINKS.map((l) => (
            <li key={l.href}>
              <Link href={l.href} className="text-sm text-uv hover:underline">
                {l.label}
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
