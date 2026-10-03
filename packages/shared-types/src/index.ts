/** Convenience types + re-export of generated OpenAPI types. */

export type { paths, components } from "./openapi";

export type Decision = "allow" | "sanitize" | "quarantine" | "block" | "escalate";

export type VerdictWord =
  | "Allowed"
  | "Sanitised"
  | "Quarantined"
  | "Blocked"
  | "Needs review";

export const DECISION_LABEL: Record<Decision, VerdictWord> = {
  allow: "Allowed",
  sanitize: "Sanitised",
  quarantine: "Quarantined",
  block: "Blocked",
  escalate: "Needs review",
};

export interface FixtureMeta {
  id: string;
  title: string;
  file: string;
  source_type: string;
  attack_types: string[];
  label: string;
  note?: string;
}

export interface DemoRunResult {
  fixture_id: string;
  lane: "off" | "on";
  outcome: {
    harmed: boolean;
    canary_leaked: boolean;
    unauthorized_send: boolean;
    unauthorized_read: boolean;
    memory_poisoned: boolean;
    role_hijacked: boolean;
    task_completed: boolean;
  };
  steps: Array<Record<string, unknown>>;
}
