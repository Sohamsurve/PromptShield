"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

const ITEMS = [
  { href: "/", label: "Console" },
  { href: "/arena", label: "Arena" },
  { href: "/scans", label: "Scans" },
  { href: "/coverage", label: "Coverage" },
  { href: "/policy", label: "Policy" },
  { href: "/redteam", label: "Red team" },
  { href: "/eval", label: "Eval" },
  { href: "/settings", label: "Settings" },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const router = useRouter();

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  if (!open) return null;
  const filtered = ITEMS.filter((i) => i.label.toLowerCase().includes(q.toLowerCase()));

  return (
    <div
      className="fixed inset-0 z-50 bg-ink/40 flex items-start justify-center pt-[15vh]"
      role="dialog"
      aria-label="Command palette"
      onClick={() => setOpen(false)}
    >
      <div
        className="w-full max-w-md rounded-panel border border-rule bg-surface shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <input
          autoFocus
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Jump to… (⌘K)"
          className="w-full border-b border-rule bg-transparent px-3 py-2 text-sm outline-none"
        />
        <ul className="max-h-64 overflow-auto py-1">
          {filtered.map((item) => (
            <li key={item.href}>
              <button
                type="button"
                className="w-full text-left px-3 py-2 text-sm hover:bg-paper"
                onClick={() => {
                  router.push(item.href);
                  setOpen(false);
                }}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
