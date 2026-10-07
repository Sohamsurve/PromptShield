const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export function apiBase() {
  return API_BASE;
}

export async function fetchFixtures() {
  const r = await fetch(`${API_BASE}/v1/demo/fixtures`, { cache: "no-store" });
  if (!r.ok) throw new Error(`fixtures ${r.status}`);
  return r.json();
}

export async function runDemo(
  fixtureId: string,
  lanes: Array<"off" | "on"> = ["off", "on"],
  opts?: { textScanning?: boolean },
) {
  const r = await fetch(`${API_BASE}/v1/demo/run`, {
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
  const r = await fetch(`${API_BASE}/v1/scans?limit=${limit}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`scans ${r.status}`);
  return r.json();
}

export async function fetchScan(scanId: string) {
  const r = await fetch(`${API_BASE}/v1/scans/${encodeURIComponent(scanId)}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`scan ${r.status}`);
  return r.json();
}

export async function postScan(content: string, sourceType = "text") {
  const r = await fetch(`${API_BASE}/v1/scan`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ source_type: sourceType, content, trust: 3 }),
  });
  if (!r.ok) throw new Error(`scan ${r.status}`);
  return r.json();
}

export async function fetchEvalLatest() {
  const r = await fetch(`${API_BASE}/v1/eval/latest`, { cache: "no-store" });
  if (!r.ok) throw new Error(`eval/latest ${r.status}`);
  return r.json();
}

export async function fetchHealthz() {
  const r = await fetch(`${API_BASE}/v1/healthz`, { cache: "no-store" });
  if (!r.ok) throw new Error(`healthz ${r.status}`);
  return r.json() as Promise<{
    judge_mode?: string;
    api_key_configured?: boolean;
    model?: string;
    status?: string;
  }>;
}

export async function fetchPolicy() {
  const r = await fetch(`${API_BASE}/v1/policy`, { cache: "no-store" });
  if (!r.ok) throw new Error(`policy ${r.status}`);
  return r.json();
}

export async function savePolicy(policy: Record<string, unknown>, note = "") {
  const r = await fetch(`${API_BASE}/v1/policy`, {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ ...policy, note }),
  });
  if (!r.ok) throw new Error(`policy PUT ${r.status}`);
  return r.json();
}

export async function fetchPolicyDiff(a: number, b: number) {
  const r = await fetch(`${API_BASE}/v1/policy/diff?a=${a}&b=${b}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`policy/diff ${r.status}`);
  return r.json();
}

export async function policyTest(content: string, sourceType = "text") {
  const r = await fetch(`${API_BASE}/v1/policy/test`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ content, source_type: sourceType, trust: 1 }),
  });
  if (!r.ok) throw new Error(`policy/test ${r.status}`);
  return r.json();
}

export async function policyReplay(sources: Record<string, unknown>) {
  const r = await fetch(`${API_BASE}/v1/policy/replay`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ sources }),
  });
  if (!r.ok) throw new Error(`policy/replay ${r.status}`);
  return r.json();
}

export function wsUrl(path: string) {
  const base = API_BASE.replace(/^http/, "ws");
  return `${base}/v1${path}`;
}
