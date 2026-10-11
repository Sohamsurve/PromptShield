"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { fetchHealthz, fetchMe, storeBearer } from "@/lib/api";

export default function OwnerSignInPage() {
  const router = useRouter();
  const [secret, setSecret] = useState("");
  const [demo, setDemo] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    fetchHealthz()
      .then((body) => setDemo(body.owner_sign_in === "demo"))
      .catch(() => setDemo(false));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const value = secret.trim();
    if (!value) {
      setError("Enter the admin sign-in.");
      return;
    }
    setPending(true);
    setError(null);
    try {
      const me = await fetchMe(value);
      if (me.role !== "admin") {
        setError("That sign-in is not an admin.");
        return;
      }
      storeBearer(value);
      setSecret("");
      router.push("/console");
    } catch {
      setError("That sign-in was not accepted.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="mx-auto flex w-full max-w-md flex-col gap-6 px-4 py-16 md:py-24">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Admin control</h1>
        <p className="text-sm text-muted-foreground">
          This opens admin control: scans, users, policy, eval, red team, and keys. Caller keys stay on the other sign-in.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Admin sign-in</CardTitle>
          <CardDescription>The built-in admin sign-in stays fixed. You can add more admins later.</CardDescription>
        </CardHeader>
        <form onSubmit={onSubmit}>
          <CardContent>
            <FieldGroup>
              <Field data-invalid={error ? true : undefined}>
                <FieldLabel htmlFor="owner-secret">Password or admin key</FieldLabel>
                <input
                  id="owner-secret"
                  type="password"
                  autoComplete="current-password"
                  value={secret}
                  aria-invalid={error ? true : undefined}
                  onChange={(event) => setSecret(event.target.value)}
                  className="w-full rounded-panel border-2 border-ink bg-background px-3 text-sm outline-none"
                />
                {demo ? (
                  <FieldDescription>
                    Local demo admin password: <span className="font-mono text-xs">promptshield-owner</span>
                  </FieldDescription>
                ) : (
                  <FieldDescription>
                    Use PROMPTSHIELD_OWNER_PASSWORD, the service key, or an admin key created in the console.
                  </FieldDescription>
                )}
                {error ? <FieldError>{error}</FieldError> : null}
              </Field>
            </FieldGroup>
          </CardContent>
          <CardFooter className="flex-col items-stretch">
            <Button type="submit" className="w-full" disabled={pending}>
              {pending ? "Checking" : "Open admin control"}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
