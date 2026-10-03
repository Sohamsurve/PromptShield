import { Check, X } from "lucide-react";

export function OutcomeBanner({
  harmed,
  detail,
}: {
  harmed: boolean;
  detail: string;
}) {
  return (
    <div
      className={`mt-4 flex items-center gap-2 text-sm font-medium ${
        harmed ? "text-block" : "text-allow"
      }`}
      role="status"
    >
      {harmed ? <X size={16} strokeWidth={1.5} aria-hidden /> : <Check size={16} strokeWidth={1.5} aria-hidden />}
      <span>
        {harmed ? "Harmed" : "Safe"} — {detail}
      </span>
    </div>
  );
}
