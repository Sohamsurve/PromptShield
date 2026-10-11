const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

/** Browser calls same-origin `/api/v1/*` (Next rewrite) to avoid CSP / port drift. */
function v1(path: string) {
  if (typeof window !== "undefined") {
    return `/api/v1${path}`;
  }
  return `${API_BASE}/v1${path}`;
}

export function apiBase() {
  return typeof window !== "undefined" ? "/api/v1 (proxied)" : API_BASE;
}

const BEARER_KEY = "ps_bearer";

export function storedBearer(): string {
  if (typeof window === "undefined") return "";
  return sessionStorage.getItem(BEARER_KEY) || "";
}

export function storeBearer(token: string) {
  sessionStorage.setItem(BEARER_KEY, token);
}

export function clearBearer() {
  sessionStorage.removeItem(BEARER_KEY);
}

function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  const token = storedBearer();
  if (token && !headers.has("authorization") && !headers.has("x-api-key")) {
    headers.set("authorization", `Bearer ${token}`);
  }
  return fetch(v1(path), { ...init, headers });
}

export async function fetchFixtures() {
  const r = await apiFetch("/demo/fixtures", { cache: "no-store" });
  if (!r.ok) throw new Error(`fixtures ${r.status}`);
  return r.json();
}

export async function runDemo(
  fixtureId: string,
  lanes: Array<"off" | "on"> = ["off", "on"],
  opts?: { textScanning?: boolean },
) {
  const r = await apiFetch("/demo/run", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      fixture_id: fixtureId,
      lanes,
      text_scanning: opts?.textScanning ?? true,
    }),
  });
  if (!r.ok) throw new Error(`demo/run ${r.status}`);
  return r.json();
}

export async function fetchScans(limit = 50) {
  const r = await apiFetch(`/scans?limit=${limit}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`scans ${r.status}`);
  return r.json();
}

export async function fetchScan(scanId: string) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 20_000);
  try {
    const r = await apiFetch(`/scans/${encodeURIComponent(scanId)}`, {
      cache: "no-store",
      signal: ctrl.signal,
    });
    if (!r.ok) throw new Error(`scan ${r.status}`);
    return r.json();
  } catch (e) {
    if (e instanceof Error && e.name === "AbortError") {
      throw new Error("scan timeout");
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
}

export async function postScan(content: string, sourceType = "text") {
  const r = await apiFetch("/scan", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ source_type: sourceType, content, trust: 3 }),
  });
  if (!r.ok) throw new Error(`scan ${r.status}`);
  return r.json();
}

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

/** Upload a hostile specimen via POST /v1/scan/file (multipart). */
export async function postScanFile(file: File, sourceType?: string) {
  if (file.size > MAX_UPLOAD_BYTES) {
    throw new Error("file too large (10 MB max)");
  }
  const body = new FormData();
  // Sanitize display name for the upload field only; server re-infers type from filename.
  const safeName = (file.name || "upload.bin").replace(/[^\w.\-()+ ]+/g, "_").slice(0, 180);
  body.append("file", file, safeName);
  if (sourceType) body.append("source_type", sourceType);
  body.append("trust", "3");
  const r = await apiFetch("/scan/file", { method: "POST", body });
  if (!r.ok) {
    let detail = `scan/file ${r.status}`;
    try {
      const j = await r.json();
      if (j?.detail) detail = String(j.detail);
    } catch {
      /* keep status */
    }
    throw new Error(detail);
  }
  return r.json();
}

/** Append a labelled bypass case to the local regression queue (add-only; not sealed). */
export async function addRegressionCase(body: {
  content: string;
  label?: string;
  scan_id?: string;
  decision?: string;
}) {
  const r = await apiFetch("/redteam/regression", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`regression ${r.status}`);
  return r.json();
}

export async function fetchEvalLatest() {
  const r = await apiFetch("/eval/latest", { cache: "no-store" });
  if (!r.ok) throw new Error(`eval/latest ${r.status}`);
  return r.json();
}

export async function fetchEvalRuns() {
  const r = await apiFetch("/eval/runs", { cache: "no-store" });
  if (!r.ok) throw new Error(`eval/runs ${r.status}`);
  return r.json() as Promise<{ on_disk?: Array<{ id: string; path: string }>; in_memory?: unknown[] }>;
}

export async function startEvalRun(mode: "fast" | "full" = "fast") {
  const r = await apiFetch("/eval/run", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  if (!r.ok) throw new Error(`eval/run ${r.status}`);
  return r.json() as Promise<{ eval_run_id: string; status?: string }>;
}

export async function fetchEvalRun(id: string) {
  const r = await apiFetch(`/eval/runs/${encodeURIComponent(id)}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`eval/run ${r.status}`);
  return r.json();
}

export async function fetchHealthz() {
  const r = await apiFetch("/healthz", { cache: "no-store" });
  if (!r.ok) throw new Error(`healthz ${r.status}`);
  return r.json() as Promise<{
    status?: string;
    judge_mode?: string;
    judge_model?: string;
    llm_provider?: string;
    api_key_configured?: boolean;
    judge_timeout_ms?: number;
    judge_reasoning_effort?: string;
    firewall_auth?: "demo" | "api_key";
    firewall_key_configured?: boolean;
    owner_sign_in?: "demo" | "configured" | "unset";
  }>;
}

export async function fetchPolicy() {
  const r = await apiFetch("/policy", { cache: "no-store" });
  if (!r.ok) throw new Error(`policy ${r.status}`);
  return r.json();
}

export async function savePolicy(policy: Record<string, unknown>, note = "") {
  const r = await apiFetch("/policy", {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ ...policy, note }),
  });
  if (!r.ok) throw new Error(`policy PUT ${r.status}`);
  return r.json();
}

export async function fetchPolicyDiff(a: number, b: number) {
  const r = await apiFetch(`/policy/diff?a=${a}&b=${b}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`policy/diff ${r.status}`);
  return r.json();
}

export async function policyTest(content: string, sourceType = "text") {
  const r = await apiFetch("/policy/test", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ content, source_type: sourceType, trust: 1 }),
  });
  if (!r.ok) throw new Error(`policy/test ${r.status}`);
  return r.json();
}

export async function policyReplay(sources: Record<string, unknown>) {
  const r = await apiFetch("/policy/replay", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ sources }),
  });
  if (!r.ok) throw new Error(`policy/replay ${r.status}`);
  return r.json();
}

export async function resetPolicy() {
  const r = await apiFetch("/policy/reset", { method: "POST" });
  if (!r.ok) throw new Error(`policy/reset ${r.status}`);
  return r.json();
}

export async function applyPolicyPreset(name: "balanced" | "low_false_alarms") {
  const r = await apiFetch(`/policy/preset/${name}`, { method: "POST" });
  if (!r.ok) throw new Error(`policy/preset ${r.status}`);
  return r.json();
}

export type Caller = {
  role: "admin" | "user" | "demo";
  name: string;
  prefix: string;
  key_id: string | null;
  scan_count: number;
};

export async function fetchMe(token?: string): Promise<Caller> {
  const headers = token ? { authorization: `Bearer ${token}` } : undefined;
  const r = await apiFetch("/me", { cache: "no-store", headers });
  if (!r.ok) throw new Error(`me ${r.status}`);
  return r.json();
}

export async function fetchAccounts() {
  const r = await apiFetch("/accounts", { cache: "no-store" });
  if (!r.ok) throw new Error(`accounts ${r.status}`);
  return r.json() as Promise<{
    items: Array<{
      email: string;
      name: string;
      prefix: string;
      created_at: number;
      keys_active: number;
      keys_total: number;
      scans: number;
      last_scan_at: number | null;
      decisions: Partial<Record<string, number>>;
    }>;
  }>;
}

export async function fetchKeys() {
  const r = await apiFetch("/keys", { cache: "no-store" });
  if (!r.ok) throw new Error(`keys ${r.status}`);
  return r.json() as Promise<{
    items: Array<{ key_id: string; name: string; prefix: string; role: string; created_at: number; revoked: boolean }>;
  }>;
}

export async function createKey(name: string, role: "user" | "admin" = "user") {
  const r = await apiFetch("/keys", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ name, role }),
  });
  if (!r.ok) throw new Error(`keys ${r.status}`);
  return r.json() as Promise<{ key_id: string; name: string; prefix: string; token: string }>;
}

export async function fetchMyKeys() {
  const r = await apiFetch("/me/keys", { cache: "no-store" });
  if (!r.ok) throw new Error(`me/keys ${r.status}`);
  return r.json() as Promise<{
    items: Array<{
      key_id: string;
      name: string;
      prefix: string;
      role: string;
      created_at: number;
      revoked: boolean;
      primary?: boolean;
    }>;
  }>;
}

export async function createMyKey(name: string) {
  const r = await apiFetch("/me/keys", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ name }),
  });
  if (!r.ok) throw new Error(`me/keys ${r.status}`);
  return r.json() as Promise<{ key_id: string; name: string; prefix: string; token: string }>;
}

export async function revokeMyKey(keyId: string) {
  const r = await apiFetch(`/me/keys/${encodeURIComponent(keyId)}/revoke`, { method: "POST" });
  if (!r.ok) throw new Error(`me/keys revoke ${r.status}`);
  return r.json();
}

export async function revokeKey(keyId: string) {
  const r = await apiFetch(`/keys/${encodeURIComponent(keyId)}/revoke`, { method: "POST" });
  if (!r.ok) throw new Error(`revoke ${r.status}`);
  return r.json();
}

export function wsUrl(path: string) {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}/v1${path}`;
}
