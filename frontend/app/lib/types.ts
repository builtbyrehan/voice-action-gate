export type ParamSource =
  | "USER_EXPLICIT"
  | "SYSTEM_CONTEXT"
  | "AI_INFERENCE"
  | "DEFAULT_VALUE"
  | "UNCERTAIN"
  | "UNKNOWN";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export type GateDecision =
  | "AUTHORIZED"
  | "NEEDS_CLARIFICATION"
  | "NEEDS_CONFIRMATION"
  | "BLOCKED";

export type Phase = "IDLE" | "ACTION_PENDING" | "CONFIRMATION_PENDING" | "COMPLETED";

export interface ParamEvidence {
  name: string;
  value?: string;
  quote?: string;
  claimed_source: ParamSource;
  source: ParamSource;
  verified: boolean;
  uncertain: boolean;
  confidence: number;
  candidates: string[];
}

export interface GateCheck {
  check: string;
  passed: boolean;
  detail?: string;
}

export interface GateResult {
  decision: GateDecision;
  action?: string;
  risk?: RiskLevel;
  checks: GateCheck[];
  reasons: string[];
  missing: string[];
  ambiguous: Record<string, string[]>;
  unverified: string[];
  evidence: ParamEvidence[];
}

export interface TurnOutcome {
  reply: string;
  phase: Phase;
  gate?: GateResult;
  tool_result?: {
    status: string;
    result: Record<string, unknown>;
  };
}

export interface ActionSchema {
  name: string;
  description: string;
  risk: RiskLevel;
  required_params: string[];
  requires_confirmation: boolean;
}

export interface AuditEntry {
  timestamp: string;
  action: string;
  parameters: Record<string, string>;
  sources: Record<string, string>;
  risk: string;
  confirmation: boolean;
  decision: string;
  reason?: string;
  tool_result?: {
    status: string;
    result: Record<string, unknown>;
  };
}
