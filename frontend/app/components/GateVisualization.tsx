"use client";

import { GateCheck } from "../lib/types";

export default function GateVisualization({
  checks,
}: {
  checks: GateCheck[];
}) {
  if (checks.length === 0) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-zinc-600 dark:text-zinc-400 uppercase tracking-wide">
        Gate Checks
      </h3>
      <div className="flex flex-wrap gap-2">
        {checks.map((c) => (
          <div
            key={c.check}
            className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm ${
              c.passed
                ? "border-emerald-200 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-900/20"
                : "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20"
            }`}
          >
            <span
              className={`text-lg ${
                c.passed
                  ? "text-emerald-600 dark:text-emerald-400"
                  : "text-red-600 dark:text-red-400"
              }`}
            >
              {c.passed ? "\u2713" : "\u2717"}
            </span>
            <div>
              <div className="font-medium text-zinc-900 dark:text-zinc-100">
                {c.check.replace("_", " ")}
              </div>
              {c.detail && (
                <div className="text-xs text-zinc-500 dark:text-zinc-400">
                  {c.detail}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
