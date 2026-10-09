import type { NextConfig } from "next";

const internalApi = process.env.INTERNAL_API_URL ?? "http://127.0.0.1:8000";

const isDev = process.env.NODE_ENV !== "production";
const scriptSrc = isDev ? "script-src 'self' 'unsafe-inline' 'unsafe-eval'" : "script-src 'self'";
const styleSrc = isDev ? "style-src 'self' 'unsafe-inline'" : "style-src 'self'";

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
            value: `default-src 'self'; connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; img-src 'self' data:; ${styleSrc}; ${scriptSrc}; font-src 'self' data:; frame-ancestors 'none'; base-uri 'self'`,
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
