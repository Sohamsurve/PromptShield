"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
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
  Plug,
  Moon,
  Sun,
  Menu,
  KeyRound,
  Users,
} from "lucide-react";
import { ConnectionDot } from "@/components/connection-dot";
import { CommandPalette } from "@/components/command-palette";
import { Button } from "@/components/ui/button";
import { clearBearer, fetchMe, storedBearer } from "@/lib/api";

const NAV = [
  { href: "/console", label: "Console", icon: LayoutDashboard },
  { href: "/arena", label: "Arena", icon: Crosshair },
  { href: "/scans", label: "Scans", icon: List },
  { href: "/coverage", label: "Coverage", icon: Grid3X3 },
  { href: "/policy", label: "Policy", icon: Settings2 },
  { href: "/redteam", label: "Red team", icon: Skull },
  { href: "/eval", label: "Eval", icon: CheckCircle2 },
  { href: "/integrate", label: "Integrate", icon: Plug },
  { href: "/keys", label: "Keys", icon: KeyRound },
  { href: "/users", label: "Users", icon: Users },
  { href: "/settings", label: "Settings", icon: Menu },
];

const USER_NAV = [
  { href: "/portal", label: "Dashboard", icon: LayoutDashboard },
  { href: "/portal/scans", label: "Scans", icon: List },
  { href: "/portal/arena", label: "Arena", icon: Crosshair },
  { href: "/portal/coverage", label: "Coverage", icon: Grid3X3 },
  { href: "/portal/redteam", label: "Red team", icon: Skull },
  { href: "/portal/keys", label: "API keys", icon: KeyRound },
  { href: "/integrate", label: "Integrate", icon: Plug },
];

function BrandMark() {
  return (
    <img src="/assets/favicon-128.png" alt="" width={32} height={32} className="size-8 shrink-0" />
  );
}

const PUBLIC_PATHS = ["/", "/login", "/signup", "/admin", "/owner"];
const ADMIN_PREFIXES = ["/console", "/arena", "/scans", "/coverage", "/policy", "/redteam", "/eval", "/settings", "/keys", "/users"];

function callerRedirect(pathname: string) {
  if (pathname === "/arena" || pathname.startsWith("/arena/")) return "/portal/arena";
  if (pathname === "/coverage" || pathname.startsWith("/coverage/")) return "/portal/coverage";
  if (pathname === "/redteam" || pathname.startsWith("/redteam/")) return "/portal/redteam";
  return "/portal";
}

const MORE_PATHS = ["/policy", "/redteam", "/scans", "/settings", "/integrate", "/keys", "/users"];

function linkActive(href: string, pathname: string, more = false) {
  if (href === "/portal") return pathname === "/portal";
  if (more && href === "/settings" && MORE_PATHS.includes(pathname)) return true;
  return pathname === href || (href !== "/" && pathname.startsWith(`${href}/`));
}

const MOBILE_NAV = [
  { href: "/console", label: "Console", icon: LayoutDashboard },
  { href: "/arena", label: "Arena", icon: Crosshair },
  { href: "/coverage", label: "Coverage", icon: Grid3X3 },
  { href: "/eval", label: "Eval", icon: CheckCircle2 },
  { href: "/settings", label: "More", icon: Menu },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [limited, setLimited] = useState(false);
  const [role, setRole] = useState<"demo" | "admin" | "user">("demo");
  const [ready, setReady] = useState(false);
  useEffect(() => setMounted(true), []);
  useEffect(() => {
    fetch("/api/v1/healthz")
      .then((r) => r.json())
      .then((body) => setLimited(body?.judge_mode !== "live"))
      .catch(() => setLimited(true));
  }, []);
  useEffect(() => {
    const token = storedBearer();
    if (!token) {
      setRole("demo");
      setReady(true);
      return;
    }
    fetchMe()
      .then((me) => setRole(me.role === "user" || me.role === "admin" ? me.role : "demo"))
      .catch(() => {
        clearBearer();
        setRole("demo");
      })
      .finally(() => setReady(true));
  }, [pathname]);
  useEffect(() => {
    if (!ready) return;
    const adminPath = ADMIN_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
    if (role === "user" && adminPath) router.replace(callerRedirect(pathname));
    if (role !== "admin" && role !== "user" && adminPath) router.replace("/admin");
  }, [ready, role, pathname, router]);
  // resolvedTheme is only known after mount (system / saved preference).
  // Rendering it during SSR disagrees with the client and breaks hydration.
  const dark = mounted && resolvedTheme === "dark";
  const nav = role === "user" ? USER_NAV : NAV;
  const mobileNav = role === "user" ? USER_NAV : MOBILE_NAV;
  const publicPage = PUBLIC_PATHS.includes(pathname);
  const landing = pathname === "/";
  const callerPublic = landing || pathname === "/login" || pathname === "/signup";
  // Admin sign-in stays on the dark shell. The landing, sign-in, and sign-up share the white neo-brutal theme.
  const publicDark = callerPublic ? !mounted || dark : true;

  function signOut() {
    clearBearer();
    setRole("demo");
    router.push("/");
  }

  if (publicPage || (role !== "admin" && role !== "user")) {
    return (
      <div className={`${publicDark ? "dark " : ""}h-screen flex flex-col overflow-hidden bg-background text-foreground`}>
        <header className="shrink-0 border-b-2 border-ink bg-background">
          <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between gap-3 px-4">
            <Link href="/" className="flex items-center gap-2 font-bold tracking-tight">
              <BrandMark />
              PromptShield
            </Link>
            <nav className="flex items-center gap-2" aria-label="Public">
              {callerPublic && mounted ? (
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
                  onClick={() => setTheme(dark ? "light" : "dark")}
                >
                  {dark ? <Sun aria-hidden /> : <Moon aria-hidden />}
                </Button>
              ) : null}
              {role === "admin" ? (
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/console">Console</Link>
                </Button>
              ) : null}
              {role === "user" ? (
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/portal">My scans</Link>
                </Button>
              ) : null}
              {role === "demo" && landing ? (
                <>
                  <Button size="sm" variant="outline" asChild>
                    <Link href="/login">Sign in</Link>
                  </Button>
                  <Button size="sm" asChild>
                    <Link href="/signup">Create account</Link>
                  </Button>
                </>
              ) : null}
              {callerPublic ? null : (
                <Button size="sm" variant="outline" asChild>
                  <Link href="/admin">Admin</Link>
                </Button>
              )}
            </nav>
          </div>
        </header>
        <main id="main" className="site-grid relative min-w-0 flex-1 overflow-y-auto overflow-x-hidden">
          {children}
        </main>
      </div>
    );
  }

  return (
    <div
      className={`${role === "admin" ? "admin-shell " : ""}flex h-screen flex-col overflow-hidden bg-background text-foreground md:flex-row`}
    >
      <aside className="hidden h-screen w-56 shrink-0 flex-col overflow-y-auto border-r-2 border-ink bg-card md:flex">
        <div className="flex flex-col gap-1 border-b-2 border-ink px-4 py-5">
          <Link href={role === "user" ? "/portal" : "/console"} className="flex items-center gap-2 text-lg font-bold tracking-tight">
            <BrandMark />
            PromptShield
          </Link>
          <div className="text-xs text-muted-foreground">{role === "user" ? "Your account" : "Admin control"}</div>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-2" aria-label="Primary">
          {nav.map((item) => {
            const active = linkActive(item.href, pathname, false);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`flex items-center gap-2 rounded-panel px-3 py-2 text-sm ${
                  active
                    ? "border-2 border-ink bg-accent text-foreground shadow-[2px_2px_0_0_var(--ink)]"
                    : "border-2 border-transparent text-muted-foreground hover:border-ink hover:bg-accent hover:text-foreground"
                }`}
              >
                <Icon size={16} strokeWidth={1.5} aria-hidden />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="flex flex-col gap-2 border-t-2 border-ink p-3">
          <div className="flex items-center justify-between">
            <ConnectionDot />
            <Button
              type="button"
              variant="outline"
              size="icon"
              aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
              onClick={() => setTheme(dark ? "light" : "dark")}
            >
              {dark ? <Sun aria-hidden /> : <Moon aria-hidden />}
            </Button>
          </div>
          <Button type="button" variant="ghost" size="sm" onClick={signOut}>
            Sign out
          </Button>
        </div>
      </aside>

      <main id="main" className="h-screen min-w-0 flex-1 overflow-y-auto overflow-x-hidden bg-background pb-20 md:pb-0">
        {limited ? (
          <p className="border-b-2 border-ink bg-card px-4 py-2 text-xs text-ink" role="status">
            Limited detection: the judge is offline. Signatures and the classifier still run.
          </p>
        ) : null}
        {children}
      </main>
      <CommandPalette />

      <nav
        className="fixed inset-x-0 bottom-0 z-40 flex justify-around overflow-x-auto border-t-2 border-ink bg-card py-2 md:hidden"
        aria-label="Mobile"
      >
        {mobileNav.map((item) => {
          const Icon = item.icon;
          const active = linkActive(item.href, pathname, true);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={`flex shrink-0 flex-col items-center gap-1 px-2 text-[10px] whitespace-nowrap min-w-[3.5rem] ${
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
