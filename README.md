# 🛡️ Voice Action Gate

> **AI can understand your intent. It cannot invent your authorization.**

<p align="center">
  <img src="https://img.shields.io/badge/Status-Hackathon%20MVP-111111?style=for-the-badge" alt="Hackathon MVP" />
  <img src="https://img.shields.io/badge/Category-AI%20Security-111111?style=for-the-badge" alt="AI Security" />
  <img src="https://img.shields.io/badge/Interface-Real--Time%20Voice-111111?style=for-the-badge" alt="Real-Time Voice" />
  <img src="https://img.shields.io/badge/Backend-FastAPI-111111?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Frontend-Next.js-111111?style=for-the-badge&logo=nextdotjs" alt="Next.js" />
  <img src="https://img.shields.io/badge/Language-Python-111111?style=for-the-badge&logo=python" alt="Python" />
</p>

---

## ✨ Overview

**Voice Action Gate** is a real-time security and authorization layer for AI voice agents that can execute actions through tools and APIs.

Modern AI agents are good at understanding natural language, but they can also infer missing information from context. That is useful for low-risk tasks, but dangerous for sensitive or irreversible actions such as production deployments, database deletion, permission changes, or financial operations.

Voice Action Gate adds a hard verification boundary between the AI agent and the protected tool. Before execution, the system verifies what the user asked for, which parameters are required, which values were explicitly spoken, whether anything is ambiguous, the risk level of the action, and whether explicit confirmation is required.

> **Core rule:** If explicit authorization is missing, the action does not happen.

---

## 🚨 The Problem

AI systems are moving from **answering questions** to **taking real-world actions**.

A user may say:

```text
Delete the old database.
```

An AI agent may try to infer:

- which database is "old"
- which environment is intended
- whether the action should happen immediately
- whether the user truly meant to authorize deletion

That creates the central security problem:

> **AI inference ≠ user authorization**

Voice Action Gate is designed to keep task understanding separate from permission to execute.

---

## 💡 The Solution

Voice Action Gate introduces a controlled execution pipeline:

```text
User Voice
   ↓
Speech-to-Text
   ↓
Intent + Parameter Extraction
   ↓
Parameter Provenance Verification
   ↓
Risk + Ambiguity + Confirmation Checks
   ↓
ACTION GATE
   ↓
Protected Tool / API
   ↓
Audit Log
```

The most important architectural rule is simple:

> **The LLM suggests. The Gate decides.**

The AI model can interpret the request and propose structured parameters, but it cannot directly execute protected high-risk tools.

---

## 🔐 Core Security Principle

For sensitive actions, required parameters must be **explicitly provided by the user**.

### Explicit example

```text
User: Deploy version 4.8.2 to production.
```

```text
version      = 4.8.2      → USER_EXPLICIT

environment  = production → USER_EXPLICIT
```

### Inferred example

```text
User: Deploy the latest version.
```

The system may know what the latest version is, but that value came from context or inference rather than explicit user authorization.

For a high-risk action:

```text
INFERENCE ≠ AUTHORIZATION
```

---

## 🧾 Parameter Provenance

Every extracted parameter is assigned a source so the system knows **where the value came from**.

| Source | Meaning | High-Risk Authorization |
|---|---|---|
| `USER_EXPLICIT` | The user directly stated the value | ✅ Accepted |
| `SYSTEM_CONTEXT` | Retrieved from system context | ❌ Not sufficient |
| `AI_INFERENCE` | Inferred by the AI | ❌ Not sufficient |
| `DEFAULT_VALUE` | Filled using a default | ❌ Not sufficient |
| `UNKNOWN` | Source cannot be verified | ❌ Not sufficient |

For high-risk actions, required parameters must have `USER_EXPLICIT` provenance.

---

## 🧠 How Provenance Is Verified

For every important extracted parameter, the AI provides evidence from the transcript.

Example:

```text
parameter: environment
value: production
evidence: "production"
```

The verifier checks whether the quoted evidence actually appears in the user's transcript.

- Evidence found → mark as `USER_EXPLICIT`
- Evidence not found → downgrade to inference / fail safe
- Uncertain language such as *probably* or *maybe* → mark as uncertain and block for high-risk actions

This means provenance is **verified by code**, not merely claimed by the LLM.

---

## 🚦 Risk Model

Voice Action Gate classifies actions by risk.

### 🟢 Low Risk

Examples:

- search information
- view analytics
- generate reports
- read logs

Behavior:

```text
Complete parameters → Execute
```

### 🟡 Medium Risk

Examples:

- create a ticket
- restart a development service
- send an internal notification
- modify non-critical data

Behavior:

```text
Complete parameters → Validate → Execute
```

### 🔴 High Risk

Examples:

- production deployment
- database deletion
- permission modification
- account disabling
- financial transfer

Behavior:

```text
Explicit parameters
      ↓
No ambiguity
      ↓
Risk validation
      ↓
Explicit confirmation
      ↓
Execute
      ↓
Audit
```

---

## ⚙️ Action Gate Decision Engine

The Action Gate evaluates security requirements in a deterministic order.

```text
IF action does not exist:
    BLOCK

IF a required parameter is missing:
    BLOCK / ASK USER

IF a parameter is ambiguous:
    BLOCK / ASK USER

IF a high-risk parameter was inferred:
    BLOCK

IF a high-risk action requires confirmation
AND confirmation is missing:
    ASK FOR CONFIRMATION

IF all requirements pass:
    AUTHORIZE
    EXECUTE TOOL
    CREATE AUDIT LOG
```

### Possible outcomes

| Outcome | Meaning |
|---|---|
| `BLOCKED` | Request cannot safely execute |
| `ACTION_PENDING` | Required information is missing |
| `CONFIRMATION_PENDING` | Action is ready but requires explicit confirmation |
| `AUTHORIZED` | Security requirements have passed |
| `EXECUTING` | Protected tool is being invoked |
| `DONE` | Execution flow completed |

---

## 🗣️ Conversation State Flow

The session tracks where the user is in the authorization process.

```text
IDLE
  ↓
ACTION_PENDING
  ↓
CONFIRMATION_PENDING
  ↓
EXECUTING
  ↓
DONE
  ↓
IDLE
```

For high-risk actions, generic conversational responses should not automatically count as authorization. The system is designed to prefer explicit confirmation.

---

## 🎯 Supported Hackathon Actions

The MVP demonstrates three protected high-risk action types.

### 1. Deploy Application

```python
deploy_application(
    application,
    version,
    environment
)
```

**Risk:** HIGH

### 2. Delete Database

```python
delete_database(
    database,
    environment
)
```

**Risk:** HIGH

### 3. Transfer Demo Funds

```python
transfer_funds(
    amount,
    currency,
    recipient
)
```

**Risk:** HIGH

> ⚠️ Financial and destructive operations in the hackathon demo are simulated only.

---

## 🎬 Demo Flow

The demo is designed to show the system refusing to guess.

### Demo 1 — Ambiguous Request

```text
User: "Delete the old database."
```

There are multiple possible databases.

**Result:** `BLOCKED`

**Reason:** Ambiguous database.

---

### Demo 2 — Missing Parameter

```text
User: "Delete customer_db."
```

The environment is missing.

**Result:** `BLOCKED`

**Agent:** asks which environment should be used.

---

### Demo 3 — Inference / Uncertainty

```text
User: "It's probably production."
```

The value is uncertain rather than explicitly authorized.

**Result:** `BLOCKED`

This is the key security behavior: uncertain language cannot become authorization.

---

### Demo 4 — Valid Authorization

```text
User: "Production."
```

The agent summarizes the high-risk action and requests confirmation.

```text
Agent: "You want me to permanently delete customer_db in production. Do you confirm?"

User: "Yes."
```

**Result:**

```text
AUTHORIZED → EXECUTE → AUDIT
```

---

## 🏗️ System Architecture

```text
┌─────────────────────┐
│      USER VOICE     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│   Speech-to-Text    │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Intent + Parameters │
│      Extraction     │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│ Parameter Provenance│
│      Verifier       │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│     ACTION GATE     │
│ Schema • Risk       │
│ Explicitness        │
│ Ambiguity           │
│ Confirmation        │
└───────┬───────┬─────┘
        │       │
   BLOCKED   APPROVED
                ↓
       ┌─────────────────┐
       │ Protected Tools │
       │     / APIs      │
       └────────┬────────┘
                ↓
       ┌─────────────────┐
       │    AUDIT LOG    │
       └─────────────────┘
```

### Security boundary

Protected tools are reachable **only through the Action Gate**. There is no direct execution path from the LLM to the protected tools.

---

## 🧩 Backend Components

| Component | Responsibility |
|---|---|
| Voice Handler | Receives audio and produces text |
| LLM Extractor | Extracts action, parameters, and evidence |
| Provenance Verifier | Checks whether extracted values were actually stated |
| Action Gate | Deterministic authorization and policy enforcement |
| Session Manager | Tracks multi-turn clarification and confirmation state |
| Protected Tools | Simulated high-risk actions used in the demo |
| Audit Recorder | Stores authorization and execution decisions |
| Database Layer | Stores actions, executions, evidence, and audit events |

---

## 📡 Real-Time Communication

The architecture uses separate WebSocket channels for audio and live dashboard events.

| Connection | Purpose |
|---|---|
| `/ws/audio` | Sends microphone audio and returns voice-related responses |
| `/ws/events` | Streams transcript, gate decisions, audit events, and session state |

A text-input fallback can use the same security pipeline while skipping only the voice-input step.

---

## 🖥️ Live Security Dashboard

The dashboard is designed to make authorization decisions visible in real time.

It can display:

- live conversation transcript
- detected action
- extracted parameters
- provenance / explicitness state
- risk level
- missing parameters
- gate decision
- block reason
- confirmation state
- execution status
- audit events

The goal is for a first-time viewer to understand what the system is protecting and why an action was allowed or blocked.

---

## 🧱 Technology Stack

### Frontend

- **Next.js**
- **React**
- **Tailwind CSS**
- **WebSockets** for live state updates

### Backend

- **Python**
- **FastAPI**
- **WebSockets**

### Voice

- **AssemblyAI**
- Real-time speech recognition
- Voice-agent interaction flow

### AI / NLU

- LLM with structured output
- Function / tool calling
- JSON schema validation

### Database

- **SQLite** for the hackathon MVP
- Architecture designed to support **PostgreSQL** later

---

## 📁 Backend Structure

```text
backend/app/
├── main.py          # App startup and composition
├── schemas.py       # Request/response and internal data models
├── voice/           # Speech-to-text and voice handling
├── nlu/             # LLM extraction + provenance verification
├── gate/            # Action Gate rules engine + action schemas
├── session/         # Conversation/session state
├── tools/           # Simulated protected tools
├── audit/           # Audit recording
└── db/              # Database models and persistence
```

---

## 🧪 Security Requirements

Voice Action Gate is designed around the following requirements:

- AI must never directly execute protected high-risk tools.
- High-risk parameters must have explicit user provenance.
- Missing parameters must fail closed.
- Ambiguous parameters must not be automatically resolved for high-risk actions.
- High-risk actions require confirmation when configured.
- Every authorization decision must be logged.
- The system must distinguish user statements from context, inference, and defaults.
- Demo financial and destructive operations must remain simulated.
- If validation cannot be completed, the system should not execute.
- Blocked actions should provide a human-readable reason.
- Secrets should not appear in the UI or logs.

---

## 🧾 Auditability

Every action attempt should create a traceable record.

Example authorized decision:

```json
{
  "action": "DELETE_DATABASE",
  "parameters": {
    "database": "customer_db",
    "environment": "production"
  },
  "sources": {
    "database": "USER_EXPLICIT",
    "environment": "USER_EXPLICIT"
  },
  "risk": "HIGH",
  "confirmation": true,
  "decision": "AUTHORIZED"
}
```

Example blocked decision:

```json
{
  "action": "DELETE_DATABASE",
  "decision": "BLOCKED",
  "reason": "Missing explicit environment"
}
```

---

## 🧭 Why Voice Action Gate Is Different

A traditional agent often follows this model:

```text
UNDERSTAND → EXECUTE
```

Voice Action Gate introduces a safer sequence:

```text
UNDERSTAND → VERIFY → PROVE → CONFIRM → EXECUTE
```

The product treats the user's words as **authorization evidence**, not merely conversational context.

That makes Voice Action Gate less like another AI assistant and more like an **authorization firewall for autonomous agents**.

---

## 👥 Target Users

Voice Action Gate is designed for teams using AI agents in workflows where mistakes can have operational or security consequences.

### Developers

- development tools
- repositories
- deployments
- database operations

### DevOps / SRE Teams

- application deployments
- service restarts
- infrastructure actions
- container operations

### IT Administrators

- account management
- permission changes
- configuration changes

### Enterprise Operators

- business workflows that require clear authorization and traceability

---

## ✅ Hackathon Success Criteria

The MVP is successful when it can demonstrate that:

- all high-risk demo actions pass through the Action Gate
- unauthorized simulated execution does not occur
- blocked actions provide clear reasons
- supported parameters are extracted successfully
- missing and ambiguous inputs trigger clarification
- explicit confirmation works for high-risk actions
- approved simulated tools execute only after authorization
- authorization decisions are recorded in an audit trail
- the live dashboard exposes the security state clearly

---

## 🛣️ Product Roadmap

### Phase 1 — Hackathon MVP

- real-time voice interaction
- three protected actions
- action schemas
- provenance tracking
- risk classification
- confirmation flow
- audit log
- live security dashboard

### Phase 2 — Developer Platform

- SDK
- REST API
- custom action schemas
- webhooks
- authentication
- role-based policies

### Phase 3 — Enterprise

- SSO
- RBAC
- approval chains
- organization-wide policies
- SIEM integration
- compliance reporting
- multi-agent authorization

### Phase 4 — Universal Agent Security Layer

Support authorization for:

- voice agents
- chat agents
- autonomous agents
- computer-use agents
- API agents

The long-term vision is a reusable policy-enforcement layer for AI agents.

---

## 🏁 Final Positioning

**Voice Action Gate** exists for a world where AI systems do more than generate answers—they perform actions.

The challenge is no longer only:

> *Can the AI perform the task?*

It is also:

> *Did the user explicitly authorize this exact action?*

Voice Action Gate adds the missing enforcement boundary between AI understanding and real-world execution.

> ### **AI can understand your intent. It cannot invent your authorization.**

---

## 🏷️ Suggested Project Tags

`AI Security` · `Cybersecurity` · `Voice AI` · `Agentic AI` · `AI Agents` · `Authorization` · `FastAPI` · `Next.js` · `WebSockets` · `AssemblyAI` · `LLM` · `Auditability`

---

<p align="center">
  <strong>Voice Action Gate</strong><br/>
  Safe, explicit, traceable execution for AI agents.
</p>
