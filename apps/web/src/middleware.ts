import { NextRequest, NextResponse } from "next/server";

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
  return origins.join(" ");
}

export function middleware(request: NextRequest) {
  const isDev = process.env.NODE_ENV !== "production";
  const nonce = btoa(crypto.randomUUID());
  const scriptSrc = isDev
    ? "script-src 'self' 'unsafe-inline' 'unsafe-eval'"
    : `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'`;
  const csp = [
    "default-src 'self'",
    `connect-src ${connectSrc()}`,
    "img-src 'self' data:",
    "style-src 'self' 'unsafe-inline'",
    scriptSrc,
    "font-src 'self' data:",
    "object-src 'none'",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    isDev ? "" : "upgrade-insecure-requests",
  ]
    .filter(Boolean)
    .join("; ");

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  return response;
}

export const config = {
  matcher: [
    {
      source: "/((?!api|_next/static|_next/image|favicon.ico|assets/).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
