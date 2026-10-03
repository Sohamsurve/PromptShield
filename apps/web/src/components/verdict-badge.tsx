import { Check, Ban, ShieldAlert, Eraser, HelpCircle } from "lucide-react";
import type { Decision, VerdictWord } from "@promptshield/shared-types";
import { DECISION_LABEL } from "@promptshield/shared-types";

const ICON: Record<Decision, typeof Check> = {
  allow: Check,
  sanitize: Eraser,
  quarantine: ShieldAlert,
  block: Ban,
  escalate: HelpCircle,
};

const COLOUR: Record<Decision, string> = {
  allow: "text-allow",
  sanitize: "text-sanitize",
  quarantine: "text-quarantine",
  block: "text-block",
  escalate: "text-escalate",
};

export function VerdictBadge({ decision }: { decision: Decision }) {
  const Icon = ICON[decision];
  const word: VerdictWord = DECISION_LABEL[decision];
  return (
    <span className={`inline-flex items-center gap-1.5 text-sm font-medium ${COLOUR[decision]}`}>
      <Icon size={16} strokeWidth={1.5} aria-hidden />
      <span>{word}</span>
    </span>
  );
}
