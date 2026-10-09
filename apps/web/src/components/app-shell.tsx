"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import {
  Crosshair,
  LayoutDashboard,
  List,
  Grid3X3,
  Settings2,
  Skull,
  CheckCircle2,
  Moon,
  Sun,
  Menu,
} from "lucide-react";
import { ConnectionDot } from "@/components/connection-dot";
import { CommandPalette } from "@/components/command-palette";

const NAV = [
  { href: "/", label: "Console", icon: LayoutDashboard },
  { href: "/arena", label: "Arena", icon: Crosshair },
  { href: "/scans", label: "Scans", icon: List },
  { href: "/coverage", label: "Coverage", icon: Grid3X3 },
  { href: "/policy", label: "Policy", icon: Settings2 },
  { href: "/redteam", label: "Red team", icon: Skull },
  { href: "/eval", label: "Eval", icon: CheckCircle2 },
  { href: "/settings", label: "Settings", icon: Menu },
];

const MOBILE_NAV = [
  { href: "/", label: "Console", icon: LayoutDashboard },
  { href: "/arena", label: "Arena", icon: Crosshair },
  { href: "/coverage", label: "Coverage", icon: Grid3X3 },
  { href: "/eval", label: "Eval", icon: CheckCircle2 },
  { href: "/settings", label: "More", icon: Menu },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [limited, setLimited] = useState(false);
  useEffect(() => setMounted(true), []);
  useEffect(() => {
    fetch("/api/v1/healthz")
      .then((r) => r.json())
      .then((body) => setLimited(body?.judge_mode !== "live"))
      .catch(() => setLimited(true));
  }, []);
  // resolvedTheme is only known after mount (system / saved preference).
  // Rendering it during SSR disagrees with the client and breaks hydration.
  const dark = mounted && resolvedTheme === "dark";

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-paper text-ink overflow-x-hidden">
      <aside className="hidden md:flex w-48 shrink-0 flex-col border-r border-rule bg-surface">
        <div className="px-4 py-5 border-b border-rule">
          <div className="text-lg font-bold tracking-tight">PromptShield</div>
          <div className="text-xs text-slate mt-1">Specimen console</div>
        </div>
        <nav className="flex-1 p-2 space-y-1" aria-label="Primary">
          {NAV.map((item) => {
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center gap-2 rounded-panel px-3 py-2 text-sm ${
                  active ? "bg-paper text-ink" : "text-slate hover:text-ink"
                }`}
              >
                <Icon size={16} strokeWidth={1.5} aria-hidden />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="p-3 border-t border-rule flex items-center justify-between">
          <ConnectionDot />
          <button
            type="button"
            aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
            className="p-2 rounded-panel border border-rule"
            onClick={() => setTheme(dark ? "light" : "dark")}
          >
            {dark ? <Sun size={16} aria-hidden /> : <Moon size={16} aria-hidden />}
          </button>
        </div>
      </aside>

      <main id="main" className="flex-1 min-w-0 pb-20 md:pb-0">
        {limited ? (
          <p className="border-b border-rule bg-surface px-4 py-2 text-xs text-sanitize" role="status">
            Limited detection: the judge is offline. Signatures and the classifier still run.
          </p>
        ) : null}
        {children}
      </main>
      <CommandPalette />

      <nav
        className="md:hidden fixed bottom-0 inset-x-0 border-t border-rule bg-surface flex justify-around py-2 z-40"
        aria-label="Mobile"
      >
        {MOBILE_NAV.map((item) => {
          const Icon = item.icon;
          const active =
            pathname === item.href ||
            (item.href === "/settings" &&
              ["/policy", "/redteam", "/scans", "/settings"].includes(pathname));
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={`flex flex-col items-center text-[10px] gap-1 min-w-[3.5rem] ${
                active ? "text-uv" : "text-slate"
              }`}
            >
              <Icon size={18} strokeWidth={1.5} aria-hidden />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
