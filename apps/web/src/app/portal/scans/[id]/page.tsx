"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { XRayClient } from "@/app/scans/[id]/xray-client";
import { storedBearer } from "@/lib/api";

export default function UserScanPage() {
  const [ready, setReady] = useState(false);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    setSignedIn(Boolean(storedBearer()));
    setReady(true);
  }, []);

  if (!ready) {
    return (
      <p className="p-6 text-sm text-slate" role="status">
        Loading scan…
      </p>
    );
  }

  if (!signedIn) {
    return (
      <div className="space-y-3 p-6">
        <h1 className="text-xl font-bold tracking-tight">Scan</h1>
        <p className="text-sm text-slate">
          <Link href="/login" className="text-uv hover:underline">
            Sign in
          </Link>{" "}
          to open this result.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="px-4 pt-4 md:px-6">
        <Link href="/portal" className="text-sm text-uv hover:underline">
          Back to your scans
        </Link>
      </div>
      <XRayClient />
    </div>
  );
}
