"use client";

import { ParamEvidence, ParamSource } from "../lib/types";

const sourceConfig: Record<
  ParamSource,
  { icon: string; color: string }
> = {
  USER_EXPLICIT: { icon: "\u2705", color: "text-emerald-600 dark:text-emerald-400" },
  SYSTEM_CONTEXT: { icon: "\u2139\ufe0f", color: "text-blue-600 dark:text-blue-400" },
  AI_INFERENCE: { icon: "\u274c", color: "text-red-600 dark:text-red-400" },
  DEFAULT_VALUE: { icon: "\u274c", color: "text-red-600 dark:text-red-400" },
  UNCERTAIN: { icon: "\u26a0\ufe0f", color: "text-amber-600 dark:text-amber-400" },
  UNKNOWN: { icon: "\u2753", color: "text-gray-600 dark:text-gray-400" },
};

export default function ParameterTable({
  evidence,
}: {
  evidence: ParamEvidence[];
}) {
  if (evidence.length === 0) return null;

  return (
    <div className="rounded-lg border border-zinc-200 dark:border-zinc-800 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-zinc-50 dark:bg-zinc-900">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-zinc-600 dark:text-zinc-400">
              Parameter
            </th>
            <th className="px-4 py-2 text-left font-medium text-zinc-600 dark:text-zinc-400">
              Value
            </th>
            <th className="px-4 py-2 text-left font-medium text-zinc-600 dark:text-zinc-400">
              Source
            </th>
            <th className="px-4 py-2 text-left font-medium text-zinc-600 dark:text-zinc-400">
              Quote
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
          {evidence.map((e) => {
            const sc = sourceConfig[e.source];
            return (
              <tr key={e.name} className="bg-white dark:bg-zinc-950">
                <td className="px-4 py-2 font-mono text-zinc-900 dark:text-zinc-100">
                  {e.name}
                </td>
                <td className="px-4 py-2 text-zinc-700 dark:text-zinc-300">
                  {e.value || "\u2014"}
                </td>
                <td className={`px-4 py-2 font-medium ${sc.color}`}>
                  {sc.icon} {e.source.replace("_", " ")}
                </td>
                <td className="px-4 py-2 text-zinc-500 dark:text-zinc-400 italic max-w-[200px] truncate">
                  {e.quote ? `\u201c${e.quote}\u201d` : "\u2014"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
