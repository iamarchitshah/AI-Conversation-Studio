# AI Conversation Studio — Design Document
**Customer:** Global Enterprise · **Build window:** 48 hours · **Status:** Working MVP

This document accompanies these deliverables:
- `ai-conversation-studio.html` — the original self-contained prototype (mock data lives in-browser, no server needed)
- `ai-conversation-studio-connected.html` — the same UI wired to a real backend over HTTP
- `backend/` — a working FastAPI + SQLite implementation of the API design in §4 (see `backend/README.md` to run it)
- `architecture-diagram.mermaid` — the system architecture diagram

---

## 1. Problem Framing

Global Enterprise runs several AI assistants (support, sales, HR, IT) built on different
models and knowledge sources, with no shared way to see:
- whether responses are actually **grounded** in approved knowledge (hallucination risk)
- whether prompts and knowledge sources are **effective**
- what **humans think** of the answers
- whether responses comply with **policy** (PII, banned topics, escalation rules)
- how quality trends **over time and across assistants**

The Conversation Studio is a control-plane that sits alongside existing assistants and
gives one place to manage knowledge, test prompts, evaluate and explain response quality,
collect feedback, enforce governance, and report on all of it.

---

## 2. Customer Journey

The journey is written around five personas who all work inside the same Studio.

### 2.1 Knowledge Manager — "Is the assistant working from the right information?"
1. Opens **Knowledge Base** tab, sees every registered source (PDF policy, Confluence,
   HR handbook, IT wiki) with a live/stale status and last-indexed time.
2. Adds a new source or triggers re-indexing when a source goes stale (>30 days).
3. Sees chunk counts per source, giving a proxy for retrieval coverage.

### 2.2 Prompt Engineer / QA — "Does this prompt produce a trustworthy answer?"
1. Opens **Testing Playground**, picks an assistant + knowledge source.
2. Runs a prompt (or a suggested example) and gets a response back in under a second.
3. The response is annotated inline — every claim is underlined **teal (verified)**,
   **amber (unverified)**, or **red (contradicted)** against the selected source, with
   faithfulness / relevance / completeness meters and a plain-language explanation of
   *why* the score was given (which claim, which source chunk, why it failed).
4. Rates the response with a thumbs up/down, which is captured for calibration.

### 2.3 Evaluator / Reviewer — "Where should I focus attention?"
1. Opens **Evaluation Log**, a running table of every test/production response with
   automatic faithfulness and relevance scores.
2. Anything under the 70% faithfulness threshold is flagged `REVIEW`, so reviewers don't
   have to read every transcript — they triage the flagged ones.

### 2.4 Governance Owner — "Are we compliant and auditable?"
1. Opens **Governance**, sees the active policy set (PII redaction, banned-topic filter,
   faithfulness threshold, response length cap, source freshness check) and toggles them.
2. Reviews the **audit trail**: every time a policy fired, what action was taken
   (escalated / withheld / redacted) and who reviewed it — giving a defensible record.

### 2.5 Leadership / Ops — "Is this getting better or worse, and where?"
1. Opens **Analytics**, filters by assistant.
2. Sees KPI cards (conversations logged, avg. faithfulness, hallucination rate, positive
   feedback %), a 14-day faithfulness trend, hallucination rate by assistant, feedback
   sentiment split, and volume by knowledge source — enough to prioritize the next fix
   (e.g. "IT Service Bot has the highest hallucination rate — check its knowledge source
   freshness first").

---

## 3. Architecture

See `architecture-diagram.mermaid` for the full diagram. Summary of the layers:

| Layer | Responsibility |
|---|---|
| **Client** | Studio UI — dashboard, playground, KB manager, governance, feedback views |
| **API Gateway** | AuthN/Z (SSO/OIDC), rate limiting, request routing |
| **Conversation Service** | Owns session + prompt lifecycle, ties a request to a response and its evaluation |
| **Retrieval Service (RAG)** | Embeds the query, fetches relevant chunks from the Knowledge Store, returns them with source pointers used later for explainability |
| **Model Orchestrator** | Routes a prompt + retrieved context to the selected LLM adapter (mocked in this build; pluggable in production) |
| **Governance Engine** | Applies policy rules (PII redaction, banned topics, thresholds) before a response is returned; writes to the audit trail |
| **Evaluation Engine** | Scores every response for faithfulness (claim-to-source matching), relevance, and completeness; produces the human-readable explanation |
| **Feedback Service** | Captures thumbs up/down + comments, tied back to the originating conversation |
| **Analytics Service** | Aggregates evaluation + feedback + governance data into trends and KPIs |
| **Data Layer** | Knowledge Store (vector DB + metadata), Conversation & Evaluation Store (audit-ready), Feedback Store, Policy Store |
| **External / Mocked** | LLM providers behind an adapter interface; knowledge sources simulated as structured text blobs standing in for Confluence/SharePoint/PDF/Wiki connectors |

**Explainability is architectural, not bolted on**: the Retrieval Service always returns
source-chunk pointers alongside content, so the Evaluation Engine can attribute every
claim in a response back to a specific chunk (or flag it as unattributed) rather than
scoring the response as an opaque blob.

---

## 4. API Design

RESTful, JSON, versioned under `/api/v1`. Auth via bearer token (SSO-issued) on every call
in production; the MVP backend (`backend/`) implements every endpoint below against SQLite
with auth omitted for local demo purposes — see `backend/main.py`.

### Conversations
```
POST   /api/v1/conversations                 Start a conversation / run a prompt
  body: { assistantId, knowledgeSourceId, prompt }
  returns: { conversationId, response, citations[], evaluation, latencyMs, tokens }

GET    /api/v1/conversations                 List conversations (filter by assistant, date range, flagged)
GET    /api/v1/conversations/{id}            Get a single conversation with full trace
```

### Knowledge Base
```
GET    /api/v1/knowledge-sources              List sources (status, chunk count, last indexed)
POST   /api/v1/knowledge-sources               Register a new source
POST   /api/v1/knowledge-sources/{id}/reindex   Trigger re-index
DELETE /api/v1/knowledge-sources/{id}
```

### Evaluation
```
GET    /api/v1/evaluations                     List evaluated responses (filter: flagged, assistant, score range)
GET    /api/v1/evaluations/{conversationId}     Full score breakdown + explanation + cited chunks
POST   /api/v1/evaluations/{conversationId}/rescore   Re-run evaluation (e.g. after source update)
```

### Feedback
```
POST   /api/v1/feedback                         { conversationId, rating: bool, comment }
GET    /api/v1/feedback                         List feedback (filter by assistant, rating, date range)
GET    /api/v1/feedback/summary                 Aggregated satisfaction %
```

### Governance
```
GET    /api/v1/governance/policies              List policies + enabled state
PATCH  /api/v1/governance/policies/{id}          Enable/disable, edit threshold
GET    /api/v1/governance/audit-log              List policy trigger events (filter by assistant, action, date)
```

### Analytics
```
GET    /api/v1/analytics/kpis?assistantId=&range=      Summary KPI cards
GET    /api/v1/analytics/trend?metric=faithfulness&range=14d
GET    /api/v1/analytics/by-assistant?metric=hallucinationRate
GET    /api/v1/analytics/by-source?metric=volume
```

All list endpoints support `page`, `pageSize`, and standard filter query params.
All write endpoints return the created/updated resource plus a `traceId` used to
correlate logs across services for debugging and audit.

---

## 5. Key Assumptions

1. **LLMs are mocked.** The orchestrator interface (`assistantId → response`) is designed
   so a real provider (OpenAI, Anthropic, internal model) can be swapped in without
   changing any downstream evaluation, governance, or analytics code.
2. **Knowledge sources are simulated** as structured text (standing in for Confluence,
   SharePoint, PDF policy docs, internal wikis). The retrieval interface returns
   chunk-level content + a source pointer, which is the only contract downstream services
   depend on — real connectors plug in behind the same interface.
3. **Faithfulness scoring** in this MVP uses a simplified claim-to-source matching
   heuristic to demonstrate the explainability pattern (claim → chunk → verdict). A
   production system would use a dedicated NLI/entailment model or an LLM-as-judge with
   the same source-attribution contract.
4. **A response is only as auditable as its citations.** The design assumes every
   response the studio evaluates must carry retrieved-chunk references; responses
   generated outside this contract cannot be scored for faithfulness, only for
   relevance/completeness via other signals.
5. **Governance rules are declarative and centrally owned**, not hardcoded per assistant,
   so a compliance owner can change a threshold once and have it apply everywhere.
6. **Single-tenant enterprise deployment** assumed for this MVP (one org's assistants);
   multi-tenant isolation (per-business-unit data boundaries) is a next-phase concern.
7. **Human feedback is directional, not a scoring override** — thumbs up/down calibrates
   trend reporting and flags disagreement with automated scores, but doesn't silently
   overwrite the evaluation record (both are kept for audit).

---

## 6. 5-Minute Demonstration Script

**0:00–0:30 — Problem framing**
"Global Enterprise runs four assistants with no shared visibility into quality or
hallucinations. This is the Conversation Studio that fixes that."

**0:30–1:15 — Analytics (Dashboard tab)**
Open the dashboard. Point at the KPI row (conversations, faithfulness, hallucination
rate, feedback). Filter by assistant to show IT Service Bot has the highest
hallucination rate. Show the 14-day trend and volume-by-source charts — "this is where
leadership goes to prioritize."

**1:15–1:45 — Knowledge Base**
Switch to Knowledge Base. Point out the "stale" source (IT Runbook, 41 days) — "this is
likely why that assistant is hallucinating — its source hasn't been refreshed."

**1:45–3:15 — Testing Playground (the core explainability moment)**
Pick an assistant + source, run a prompt live. Walk through the annotated response:
teal = verified against source, amber/red = unverified or contradicted. Point at the
faithfulness/relevance/completeness meters and read the plain-language explanation
("2/3 claims traced to source chunks, 1 claim flagged"). Submit a thumbs-down to show
feedback capture.

**3:15–4:00 — Evaluation Log & Governance**
Show the Evaluation Log with flagged rows. Switch to Governance — toggle a policy off/on,
then show the audit trail entry created when the faithfulness threshold fired
("Escalated for review") — "this is the compliance record."

**4:00–4:45 — Feedback**
Show the Feedback tab — aggregated satisfaction %, and the thumbs-down just submitted
appearing at the top of the table with its comment.

**4:45–5:00 — Close**
"Every piece — knowledge, testing, evaluation, feedback, governance, analytics — is one
surface, backed by an API designed so the mocked LLM and simulated knowledge sources
can be swapped for production systems without changing the evaluation or governance
layer."