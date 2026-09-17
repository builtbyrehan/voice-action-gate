"use client";

import { GateDecision } from "../lib/types";

const config: Record<
  GateDecision,
  { bg: string; text: string; label: string }
> = {
  AUTHORIZED: { bg: "bg-emerald-100 dark:bg-emerald-900/30", text: "text-emerald-700 dark:text-emerald-300", label: "AUTHORIZED" },
  NEEDS_CLARIFICATION: { bg: "bg-amber-100 dark:bg-amber-900/30", text: "text-amber-700 dark:text-amber-300", label: "NEEDS CLARIFICATION" },
  NEEDS_CONFIRMATION: { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-700 dark:text-blue-300", label: "NEEDS CONFIRMATION" },
  BLOCKED: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-700 dark:text-red-300", label: "BLOCKED" },
};

export default function StatusBadge({ decision }: { decision: GateDecision }) {
  const c = config[decision];
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-semibold ${c.bg} ${c.text}`}
    >
      {c.label}
    </span>
  );
}
