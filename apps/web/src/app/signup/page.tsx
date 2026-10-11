"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { FieldError } from "@/components/ui/field";
import { AuthFields, AuthFooter, AuthLabel, AuthLink, AuthScreen, authFieldClass } from "@/components/auth-screen";
import { storeBearer } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [token, setToken] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setPending(true);
    setError(null);
    try {
      const response = await fetch("/api/v1/auth/signup", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ name: name.trim(), email: email.trim(), password }),
      });
      const body = (await response.json().catch(() => ({}))) as { token?: string; detail?: string };
      if (!response.ok) {
        setError(response.status === 409 ? "An account with that email already exists." : "Check the name, email, and password.");
        return;
      }
      const value = String(body.token || "");
      storeBearer(value);
      setPassword("");
      setConfirm("");
      setToken(value);
    } catch {
      setError("Sign-up failed.");
    } finally {
      setPending(false);
    }
  }

  async function copyToken() {
    if (!token) return;
    try {
      await navigator.clipboard.writeText(token);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  if (token) {
    return (
      <AuthScreen
        title="Account created"
        detail="Copy this API key now. It is shown once, and this browser stays signed in."
        footer={
          <>
            Already saved it? <AuthLink href="/portal">Open your scans</AuthLink>
          </>
        }
      >
        <AuthFields>
          <pre className="overflow-x-auto rounded-panel border-2 border-ink bg-background p-3 text-xs leading-relaxed">{token}</pre>
        </AuthFields>
        <AuthFooter>
          <Button type="button" variant="outline" className="w-full" onClick={copyToken}>
            {copied ? "Copied" : "Copy API key"}
          </Button>
          <Button type="button" className="w-full" onClick={() => router.push("/portal")}>
            Open your scans
          </Button>
        </AuthFooter>
      </AuthScreen>
    );
  }

  return (
    <AuthScreen
      title="Create account"
      detail="Name, email, and a password. You will get an API key for your own scans."
      footer={
        <>
          Already have an account? <AuthLink href="/login">Sign in</AuthLink>
        </>
      }
    >
      <form onSubmit={onSubmit}>
        <AuthFields>
          <div>
            <AuthLabel htmlFor="name">Name</AuthLabel>
            <input
              id="name"
              type="text"
              autoComplete="name"
              required
              value={name}
              onChange={(event) => setName(event.target.value)}
              className={authFieldClass}
            />
          </div>
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
              autoComplete="new-password"
              required
              minLength={8}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className={authFieldClass}
            />
          </div>
          <div>
            <AuthLabel htmlFor="confirm">Confirm password</AuthLabel>
            <input
              id="confirm"
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={confirm}
              onChange={(event) => setConfirm(event.target.value)}
              className={authFieldClass}
            />
          </div>
          {error ? <FieldError>{error}</FieldError> : null}
        </AuthFields>
        <AuthFooter>
          <Button type="submit" className="w-full" disabled={pending}>
            {pending ? "Creating" : "Create account"}
          </Button>
        </AuthFooter>
      </form>
    </AuthScreen>
  );
}
