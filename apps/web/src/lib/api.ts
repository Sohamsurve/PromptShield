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

export async function fetchFixtures() {
  const r = await fetch(v1("/demo/fixtures"), { cache: "no-store" });
  if (!r.ok) throw new Error(`fixtures ${r.status}`);
  return r.json();
}

export async function runDemo(
  fixtureId: string,
  lanes: Array<"off" | "on"> = ["off", "on"],
  opts?: { textScanning?: boolean },
) {
  const r = await fetch(v1("/demo/run"), {
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
  const r = await fetch(v1(`/scans?limit=${limit}`), { cache: "no-store" });
  if (!r.ok) throw new Error(`scans ${r.status}`);
  return r.json();
}

export async function fetchScan(scanId: string) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 20_000);
  try {
    const r = await fetch(v1(`/scans/${encodeURIComponent(scanId)}`), {
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
  const r = await fetch(v1("/scan"), {
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
  const r = await fetch(v1("/scan/file"), { method: "POST", body });
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
  const r = await fetch(v1("/redteam/regression"), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`regression ${r.status}`);
  return r.json();
}

export async function fetchEvalLatest() {
  const r = await fetch(v1("/eval/latest"), { cache: "no-store" });
  if (!r.ok) throw new Error(`eval/latest ${r.status}`);
  return r.json();
}

export async function fetchEvalRuns() {
  const r = await fetch(v1("/eval/runs"), { cache: "no-store" });
  if (!r.ok) throw new Error(`eval/runs ${r.status}`);
  return r.json() as Promise<{ on_disk?: Array<{ id: string; path: string }>; in_memory?: unknown[] }>;
}

export async function startEvalRun(mode: "fast" | "full" = "fast") {
  const r = await fetch(v1("/eval/run"), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  if (!r.ok) throw new Error(`eval/run ${r.status}`);
  return r.json() as Promise<{ eval_run_id: string; status?: string }>;
}

export async function fetchEvalRun(id: string) {
  const r = await fetch(v1(`/eval/runs/${encodeURIComponent(id)}`), { cache: "no-store" });
  if (!r.ok) throw new Error(`eval/run ${r.status}`);
  return r.json();
}

export async function fetchHealthz() {
  const r = await fetch(v1("/healthz"), { cache: "no-store" });
  if (!r.ok) throw new Error(`healthz ${r.status}`);
  return r.json() as Promise<{
    judge_mode?: string;
    api_key_configured?: boolean;
    model?: string;
    status?: string;
  }>;
}

export async function fetchPolicy() {
  const r = await fetch(v1("/policy"), { cache: "no-store" });
  if (!r.ok) throw new Error(`policy ${r.status}`);
  return r.json();
}

export async function savePolicy(policy: Record<string, unknown>, note = "") {
  const r = await fetch(v1("/policy"), {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ ...policy, note }),
  });
  if (!r.ok) throw new Error(`policy PUT ${r.status}`);
  return r.json();
}

export async function fetchPolicyDiff(a: number, b: number) {
  const r = await fetch(v1(`/policy/diff?a=${a}&b=${b}`), { cache: "no-store" });
  if (!r.ok) throw new Error(`policy/diff ${r.status}`);
  return r.json();
}

export async function policyTest(content: string, sourceType = "text") {
  const r = await fetch(v1("/policy/test"), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ content, source_type: sourceType, trust: 1 }),
  });
  if (!r.ok) throw new Error(`policy/test ${r.status}`);
  return r.json();
}

export async function policyReplay(sources: Record<string, unknown>) {
  const r = await fetch(v1("/policy/replay"), {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ sources }),
  });
  if (!r.ok) throw new Error(`policy/replay ${r.status}`);
  return r.json();
}

export async function resetPolicy() {
  const r = await fetch(v1("/policy/reset"), { method: "POST" });
  if (!r.ok) throw new Error(`policy/reset ${r.status}`);
  return r.json();
}

export async function applyPolicyPreset(name: "balanced" | "low_false_alarms") {
  const r = await fetch(v1(`/policy/preset/${name}`), { method: "POST" });
  if (!r.ok) throw new Error(`policy/preset ${r.status}`);
  return r.json();
}

export function wsUrl(path: string) {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}/v1${path}`;
}
