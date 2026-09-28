import type { ClaimType } from "@/types";

const STYLES: Record<ClaimType, { label: string; className: string }> = {
  fact: { label: "Fact", className: "bg-verified-dim text-verified border-verified/30" },
  inference: { label: "Inference", className: "bg-signal-dim text-signal border-signal/30" },
  recommendation: { label: "Recommendation", className: "bg-surface-raised text-paper border-line" },
};

export function ClaimBadge({ type }: { type: ClaimType }) {
  const s = STYLES[type];
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-mono uppercase tracking-wide ${s.className}`}
    >
      {s.label}
    </span>
  );
}
