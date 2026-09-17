"use client";

import { useState, useEffect } from "react";
import { TurnOutcome, AuditEntry } from "./lib/types";
import { sendTurn, getAuditLog } from "./lib/api";
import ChatInput from "./components/ChatInput";
import ConversationHistory from "./components/ConversationHistory";
import ParameterTable from "./components/ParameterTable";
import GateVisualization from "./components/GateVisualization";
import AuditLog from "./components/AuditLog";

export default function Home() {
  const [messages, setMessages] = useState<TurnOutcome[]>([]);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [sessionId] = useState(() => `demo_${Date.now()}`);

  useEffect(() => {
    // Check API health
    fetch("http://localhost:8000/api/health")
      .then((r) => r.json())
      .then(() => setConnected(true))
      .catch(() => setConnected(false));
  }, []);

  useEffect(() => {
    // Load audit log on mount and after each turn
    getAuditLog()
      .then(setAuditEntries)
      .catch(() => {});
  }, [messages.length]);

  const handleSend = async (text: string) => {
    setLoading(true);
    try {
      const outcome = await sendTurn(sessionId, text);
      setMessages((prev) => [...prev, outcome]);
    } catch (err) {
      console.error("Failed to send turn:", err);
    } finally {
      setLoading(false);
    }
  };

  const latestOutcome = messages[messages.length - 1];

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* Header */}
      <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
                Voice Action Gate
              </h1>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">
                AI can understand your intent. It cannot invent your
                authorization.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  connected ? "bg-emerald-500" : "bg-red-500"
                }`}
              />
              <span className="text-sm text-zinc-500 dark:text-zinc-400">
                {connected ? "Connected" : "Disconnected"}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Left column: Chat */}
          <div className="lg:col-span-2 space-y-6">
            {/* Conversation area */}
            <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
              <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
                Live Conversation
              </h2>
              <div className="min-h-[300px] max-h-[500px] overflow-y-auto mb-4 space-y-4">
                {messages.length === 0 ? (
                  <div className="flex items-center justify-center h-[300px] text-zinc-400 dark:text-zinc-500">
                    <div className="text-center">
                      <p className="text-lg mb-2">Start a conversation</p>
                      <p className="text-sm">
                        Try: &quot;Delete the customer database.&quot;
                      </p>
                    </div>
                  </div>
                ) : (
                  <ConversationHistory messages={messages} />
                )}
              </div>
              <ChatInput onSend={handleSend} disabled={loading} />
            </div>

            {/* Gate visualization */}
            {latestOutcome?.gate && (
              <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
                <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
                  Gate Decision
                </h2>
                <GateVisualization checks={latestOutcome.gate.checks} />
              </div>
            )}
          </div>

          {/* Right column: Parameters & Audit */}
          <div className="space-y-6">
            {/* Current parameters */}
            {latestOutcome?.gate?.evidence &&
              latestOutcome.gate.evidence.length > 0 && (
                <div className="rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6">
                  <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100 mb-4">
                    Parameter Evidence
                  </h2>
                  <ParameterTable evidence={latestOutcome.gate.evidence} />
                </div>
              )}

            {/* Audit log */}
            <AuditLog entries={auditEntries} />
          </div>
        </div>
      </main>
    </div>
  );
}
