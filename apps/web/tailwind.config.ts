import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "var(--paper)",
        surface: "var(--surface)",
        ink: "var(--ink)",
        slate: "var(--slate)",
        rule: "var(--rule)",
        uv: "var(--uv)",
        allow: "var(--allow)",
        sanitize: "var(--sanitize)",
        quarantine: "var(--quarantine)",
        block: "var(--block)",
        escalate: "var(--escalate)",
      },
      fontFamily: {
        sans: ["var(--font-hanken)", "ui-sans-serif", "system-ui"],
        mono: ["var(--font-jetbrains)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        chip: "2px",
        panel: "8px",
      },
    },
  },
  plugins: [],
};

export default config;
