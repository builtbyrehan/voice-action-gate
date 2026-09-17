"use client";

import { AuditEntry } from "../lib/types";

const decisionColor: Record<string, string> = {
  AUTHORIZED: "text-emerald-600 dark:text-emerald-400",
  BLOCKED: "text-red-600 dark:text-red-400",
  NEEDS_CLARIFICATION: "text-amber-600 dark:text-amber-400",
  NEEDS_CONFIRMATION: "text-blue-600 dark:text-blue-400",
  CANCELLED: "text-zinc-500 dark:text-zinc-400",
};

export default function AuditLog({ entries }: { entries: AuditEntry[] }) {
  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 overflow-hidden">
      <div className="bg-zinc-50 dark:bg-zinc-900 px-4 py-3 border-b border-zinc-200 dark:border-zinc-800">
        <h3 className="text-sm font-semibold text-zinc-600 dark:text-zinc-400 uppercase tracking-wide">
          Audit Trail ({entries.length} entries)
        </h3>
      </div>
      <div className="divide-y divide-zinc-100 dark:divide-zinc-800 max-h-[400px] overflow-y-auto">
        {entries.length === 0 ? (
          <div className="px-4 py-8 text-center text-zinc-500 dark:text-zinc-400">
            No audit entries yet
          </div>
        ) : (
          [...entries].reverse().map((entry, i) => (
            <div
              key={i}
              className="px-4 py-3 bg-white dark:bg-zinc-950 hover:bg-zinc-50 dark:hover:bg-zinc-900 transition-colors"
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-sm text-zinc-900 dark:text-zinc-100">
                  {entry.action}
                </span>
                <span
                  className={`text-sm font-semibold ${
                    decisionColor[entry.decision] || "text-zinc-600"
                  }`}
                >
                  {entry.decision}
                </span>
              </div>
              <div className="flex items-center gap-4 text-xs text-zinc-500 dark:text-zinc-400">
                <span>{entry.risk} risk</span>
                <span>{entry.timestamp.split("T")[1]?.split(".")[0]}</span>
                {entry.reason && (
                  <span className="truncate max-w-[200px]">
                    Reason: {entry.reason}
                  </span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
