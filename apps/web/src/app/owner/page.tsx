"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function OwnerRedirectPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/admin");
  }, [router]);
  return (
    <div className="px-4 py-16">
      <h1 className="text-2xl font-bold tracking-tight">Admin control</h1>
    </div>
  );
}
