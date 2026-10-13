import type { NextConfig } from "next";

const internalApi = process.env.INTERNAL_API_URL ?? "http://127.0.0.1:8000";

const isDev = process.env.NODE_ENV !== "production";
const scriptSrc = isDev ? "script-src 'self' 'unsafe-inline' 'unsafe-eval'" : "script-src 'self'";
const styleSrc = isDev ? "style-src 'self' 'unsafe-inline'" : "style-src 'self'";

/** Hosts the browser may call. Local dev stays open. A public API is added from the build env. */
function connectSrc(): string {
  const origins = ["'self'", "http://localhost:*", "http://127.0.0.1:*", "ws://localhost:*", "ws://127.0.0.1:*"];
  for (const raw of [process.env.NEXT_PUBLIC_API_BASE, process.env.INTERNAL_API_URL]) {
    if (!raw) continue;
    try {
      const url = new URL(raw);
      const ws = url.protocol === "https:" ? "wss:" : "ws:";
      origins.push(`${url.protocol}//${url.host}`, `${ws}//${url.host}`);
    } catch {
      /* ignore a malformed API URL */
    }
  }
  return `connect-src ${origins.join(" ")}`;
}

const nextConfig: NextConfig = {
  transpilePackages: ["@promptshield/shared-types"],
  poweredByHeader: false,
  async rewrites() {
    return [{ source: "/api/v1/:path*", destination: `${internalApi}/v1/:path*` }];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value: `default-src 'self'; ${connectSrc()}; img-src 'self' data:; ${styleSrc}; ${scriptSrc}; font-src 'self' data:; frame-ancestors 'none'; base-uri 'self'`,
          },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
};

export default nextConfig;
