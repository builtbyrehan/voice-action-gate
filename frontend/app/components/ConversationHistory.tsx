"use client";

import { TurnOutcome } from "../lib/types";
import StatusBadge from "./StatusBadge";

export default function ConversationHistory({
  messages,
}: {
  messages: TurnOutcome[];
}) {
  return (
    <div className="space-y-3">
      {messages.map((msg, i) => (
        <div key={i} className="space-y-2">
          {/* User message */}
          <div className="flex justify-end">
            <div className="max-w-[80%] rounded-lg bg-blue-600 px-4 py-2 text-sm text-white">
              {msg.reply}
            </div>
          </div>
          {/* Agent reply with gate status */}
          {msg.gate && (
            <div className="flex justify-start">
              <div className="max-w-[80%] rounded-lg bg-zinc-100 dark:bg-zinc-800 px-4 py-3 text-sm text-zinc-900 dark:text-zinc-100">
                <div className="mb-2 flex items-center gap-2">
                  <StatusBadge decision={msg.gate.decision} />
                  {msg.gate.action && (
                    <span className="text-xs text-zinc-500 dark:text-zinc-400">
                      {msg.gate.action}
                    </span>
                  )}
                </div>
                <p className="text-zinc-700 dark:text-zinc-300">{msg.reply}</p>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
