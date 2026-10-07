import type { NextConfig } from "next";

const internalApi = process.env.INTERNAL_API_URL ?? "http://127.0.0.1:8000";

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
            // 'unsafe-eval' required for Next.js / React Fast Refresh in development.
            // Without it, client components never hydrate (X-ray stuck on "Loading scan…").
            value:
              "default-src 'self'; connect-src 'self' http://localhost:* http://127.0.0.1:* ws://localhost:* ws://127.0.0.1:*; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; font-src 'self' data:;",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
