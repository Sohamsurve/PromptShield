"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { FieldError } from "@/components/ui/field";
import { AuthFields, AuthFooter, AuthLabel, AuthLink, AuthScreen, authFieldClass } from "@/components/auth-screen";
import { fetchMe, storeBearer } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const response = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      if (!response.ok) {
        setError(response.status === 401 ? "Email or password is wrong." : "Sign-in failed.");
        return;
      }
      const body = (await response.json()) as { token?: string };
      const token = String(body.token || "");
      const me = await fetchMe(token);
      storeBearer(token);
      setPassword("");
      router.push(me.role === "user" ? "/portal" : "/console");
    } catch {
      setError("Sign-in failed.");
    } finally {
      setPending(false);
    }
  }

  return (
    <AuthScreen
      title="Sign in"
      detail="Use the email and password for your account."
      footer={
        <>
          New here? <AuthLink href="/signup">Create an account</AuthLink>
        </>
      }
    >
      <form onSubmit={onSubmit}>
        <AuthFields>
          <div>
            <AuthLabel htmlFor="email">Email</AuthLabel>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className={authFieldClass}
            />
          </div>
          <div>
            <AuthLabel htmlFor="password">Password</AuthLabel>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className={authFieldClass}
            />
          </div>
          {error ? <FieldError>{error}</FieldError> : null}
        </AuthFields>
        <AuthFooter>
          <Button type="submit" className="w-full" disabled={pending}>
            {pending ? "Checking" : "Sign in"}
          </Button>
        </AuthFooter>
      </form>
    </AuthScreen>
  );
}
