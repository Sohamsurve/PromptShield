import type { NextConfig } from "next";

const internalApi = process.env.INTERNAL_API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  transpilePackages: ["@promptshield/shared-types"],
  poweredByHeader: false,
  async rewrites() {
    return [
      { source: "/favicon.ico", destination: "/assets/favicon.ico" },
      { source: "/api/v1/:path*", destination: `${internalApi}/v1/:path*` },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
};

export default nextConfig;
