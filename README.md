# 🛡️ Voice Action Gate

> *"AI can understand your intent. It cannot invent your authorization."*

**Voice Action Gate** is a real-time authorization layer for AI voice agents. It prevents sensitive actions — production deployments, database deletions, fund transfers — from being executed based on **AI-inferred or ambiguous** user intent.

An AI agent is great at filling in missing information. That's dangerous when the action is irreversible. Voice Action Gate places a **deterministic verification gate** between the AI agent and every sensitive tool: nothing executes unless the user **explicitly said** what is being executed.

---

## ⚠️ The Problem

```
User:   "Deploy the latest version."
AI infers:  app = payments-service, version = 4.8.2, environment = production
```

The AI **guessed** the application, the version, and the environment. If the guess is wrong, you just deployed the wrong build to production — or worse:

```
User:   "Delete the old database."
AI infers:  "old" probably means customer_db... or was it the backup?
```

**AI inference ≠ user authorization.**

Voice Action Gate optimizes for **safe, explicit, traceable execution** instead of task completion.

---

## 🧠 How It Works

```
User Voice / Text
        ↓
  Utterance Classifier          (action? confirmation? chitchat?)
        ↓
  Parameter Extraction          (what did the user say? — with quotes)
        ↓
  Provenance Verifier           (proves each quote exists in the transcript)
        ↓
  ┌─────────────────────────┐
  │      ACTION GATE        │   deterministic · fail-closed · no LLM
  │  schema → missing →     │
  │  ambiguity → explicit → │
  │  confirmation           │
  └─────────────────────────┘
      ↓ BLOCKED        ↓ AUTHORIZED
  ask / explain      execute tool (simulated)
        ↓                 ↓
        └──────► AUDIT LOG ◄──────┘
```

**The core rule:** the LLM only *proposes* parameters (with evidence). The Gate *verifies* the evidence with pure code. An unprovable claim is downgraded to `AI_INFERENCE` — fail closed.

### Parameter Provenance

Every parameter carries its source:

| Source | Meaning | Accepted for HIGH-risk actions? |
|---|---|---|
| `USER_EXPLICIT` | The user literally said it (quote verified) | ✅ Yes |
| `SYSTEM_CONTEXT` | Found in system data | ❌ No |
| `AI_INFERENCE` | The AI guessed it | ❌ No |
| `DEFAULT_VALUE` | A default was used | ❌ No |
| `UNCERTAIN` | Hedged ("it's *probably* production") | ❌ No |

For high-risk actions, only `USER_EXPLICIT` authorizes execution.

---

## 🎬 Demo Scenarios

| # | User says | Gate behavior |
|---|---|---|
| 1 | *"Delete the old database."* | 🔶 **Ambiguous** — 3 possible databases. Agent asks which one. Never guesses. |
| 2 | *"Delete customer_db."* | 🔶 **Missing** environment. Agent asks. |
| 3 | *"It's probably production."* | 🔴 **Inference attack blocked** — "probably" = uncertain. The key moment. |
| 4 | *"Production."* → *"Yes."* | 🟢 **AUTHORIZED** — all parameters explicit + confirmed. Tool executes (simulated), audit written. |
| — | *"Okay."* (instead of yes) | 🔴 **Rejected** — generic acks are not specific confirmation for HIGH-risk actions. |

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, Pydantic
- **Frontend:** Next.js, React, TypeScript, Tailwind CSS
- **Gate engine:** Pure deterministic Python — zero LLM, zero network
- **State:** In-memory sessions (MVP), JSONL audit trail
- **Tests:** pytest — 43 tests covering every security requirement
- **Planned:** AssemblyAI realtime voice, LLM structured-output extractor

---

## 🚀 Getting Started

### Backend

```bash
git clone https://github.com/builtbyrehan/voice-action-gate.git
cd voice-action-gate/backend

python -m venv my-venv
my-venv\Scripts\activate        # Windows  (Linux/Mac: source my-venv/bin/activate)

pip install -r requirements.txt
python -m pytest -v             # 43 tests should pass

uvicorn app.main:app --reload --port 8000
```

Interactive API docs: **http://localhost:8000/docs**

### Frontend

```bash
cd voice-action-gate/frontend

npm install
npm run dev
```

Dashboard: **http://localhost:3000**

### Try the full journey

```bash
curl -X POST localhost:8000/api/turn -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "text": "Delete the customer database."}'
# → BLOCKED: "Which environment?"

curl -X POST localhost:8000/api/turn -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "text": "Production."}'
# → Agent asks for confirmation

curl -X POST localhost:8000/api/turn -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "text": "Okay."}'
# → Rejected — generic confirmation is not enough

curl -X POST localhost:8000/api/turn -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "text": "Yes."}'
# → AUTHORIZED. Tool executed (simulated). Audit logged.
```

### API Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/turn` | POST | Conversational turn (multi-turn, stateful) |
| `/api/gate/check` | POST | Direct gate dry-run (stateless, for testing) |
| `/api/audit` | GET | Full audit trail |
| `/api/actions` | GET | Registered action schemas |
| `/api/health` | GET | Liveness |

---

## 📂 Project Structure

```
voice-action-gate/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI server
│   │   ├── schemas.py           # Evidence, gate results, decisions
│   │   ├── gate/
│   │   │   ├── actions.py       # Action schemas (3 MVP actions)
│   │   │   ├── engine.py        # ⭐ THE ACTION GATE (deterministic)
│   │   │   └── policy.py        # Confirmation policy
│   │   ├── nlu/
│   │   │   ├── extractor.py     # Utterance → parameters + quotes
│   │   │   ├── verifier.py      # Provenance verification (quote proof)
│   │   │   └── catalog.py       # Entity fixtures (databases, apps, envs)
│   │   ├── session/
│   │   │   ├── state.py         # Conversation state machine
│   │   │   └── conversation.py  # Multi-turn turn processor
│   │   ├── tools/registry.py    # Simulated tools (only reachable via the Gate)
│   │   └── audit/recorder.py    # Audit trail writer
│   └── tests/                   # 43 tests — every security requirement covered
└── frontend/
    └── app/
        ├── page.tsx             # Dashboard main page
        ├── layout.tsx           # Root layout
        ├── components/
        │   ├── ChatInput.tsx    # User input
        │   ├── ConversationHistory.tsx  # Chat messages
        │   ├── ParameterTable.tsx  # Parameter evidence display
        │   ├── GateVisualization.tsx  # Gate check status
        │   ├── AuditLog.tsx     # Audit trail display
        │   └── StatusBadge.tsx  # Decision status badge
        └── lib/
            ├── api.ts           # API client
            └── types.ts         # TypeScript types
```

**Security by construction:** the tools module has no public route. The only path to execution runs through the Gate.

---

## ✅ Security Requirements Coverage

| Requirement | Status |
|---|---|
| SR-1 — AI never directly executes protected tools | ✅ Enforced by architecture |
| SR-2 — High-risk parameters need explicit provenance | ✅ Quote verification |
| SR-3 — Missing parameters fail closed | ✅ Tested |
| SR-4 — Ambiguous params never auto-resolved | ✅ Tested |
| SR-5 — Every decision logged | ✅ Audit trail |
| SR-6 — Distinguish user statement / inference / default | ✅ Source taxonomy |
| SR-7 — Destructive/financial demos simulated | ✅ All tools simulated |

---

## 🗺️ Roadmap

- **Phase 1 — Hackathon MVP** *(in progress)*
  - [x] Deterministic Action Gate engine
  - [x] Provenance verification with quote proof
  - [x] Multi-turn conversation + clarification flow
  - [x] Explicit confirmation policy (strict for HIGH risk)
  - [x] Audit trail
  - [x] Live security dashboard (Next.js)
  - [ ] LLM-based extractor (structured output)
  - [ ] AssemblyAI realtime voice integration
- **Phase 2 — Developer Platform:** SDK, REST API, custom action schemas, webhooks
- **Phase 3 — Enterprise:** SSO, RBAC, approval chains, SIEM integration
- **Phase 4 — Universal Agent Security Layer:** voice, chat, autonomous, computer-use, API agents

---

## 📄 License

MIT

---

*Built for a hackathon. Every destructive action shown is simulated — no real databases were harmed.* 🗑️



