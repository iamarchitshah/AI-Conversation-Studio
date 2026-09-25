# AI Conversation Studio — Backend

A real FastAPI + SQLite backend implementing the API design from the challenge doc,
now serving the frontend directly so there is exactly **one thing to start and one
URL to open. It supports Supabase PostgreSQL for shared deployment data and keeps
SQLite as the zero-configuration local fallback.

## Run it (3 steps)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000
```

You can run that command either from `outputs/backend` or from the repository root.
The root launcher forwards to the active backend implementation.

## Supabase connection

Set `SUPABASE_DB_URL` to the PostgreSQL URI from Supabase Project Settings before
starting the API. The schema and expanded demo dataset are created automatically:

```powershell
$env:SUPABASE_DB_URL = "postgresql://postgres:<password>@<host>:5432/postgres"
python -m pip install -r requirements.txt
uvicorn main:app --port 8000
```

If the direct host `db.<project-ref>.supabase.co` fails with `getaddrinfo failed`,
use the **Session pooler** URI from Supabase Database Settings instead. It uses an
IPv4-compatible pooler host, typically shaped like:

```text
postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres
```

The app falls back to SQLite when Supabase is unavailable, and `/health` reports the
active database so a failed remote connection is visible without crashing startup.

When `SUPABASE_DB_URL` is absent, the app uses `DB_PATH` and SQLite. Never commit the
Supabase URI or database password; use `.env.example` as the local configuration template.

## Initialize schema and test data

The seed is idempotent. It creates the complete schema and loads ten policy/knowledge
sources, targeted employee questions, at least 60 conversations, flagged evaluations,
feedback, governance policies, and audit events:

```powershell
python scripts/seed-database.py
```

With `SUPABASE_DB_URL` set, the same command initializes Supabase. With no URL set, it
initializes the local SQLite database selected by `DB_PATH`.

Then open **http://localhost:8000** in your browser. That's it — no separate HTML
file to open, no CORS setup, no host/port mismatch. The page is served by the same
process as the API, so `connStatus` in the left nav should immediately read
"● connected to http://localhost:8000/api/v1".

## Role workflows

- **Knowledge Manager** maintains source documents, re-indexes stale sources, and keeps the knowledge base current.
- **QA Tester** runs difficult pre-live questions and inspects source grounding and trust scores.
- **Evaluator** reviews flagged answers and records an Approved, Needs changes, or Escalated decision.
- **Governance Owner** controls safety policies, thresholds, privacy protections, and the audit trail.
- **Leadership** views cross-assistant analytics, feedback, trust trends, and review volume.
- **Employee** asks the assistant questions, sees source-backed grounding, and rates answer usefulness.
- **Platform Admin** manages users and has access to every module.

The first account registered in an empty database becomes the Platform Admin. Later
accounts can select only the six operational roles; an administrator can change roles
from the Admin module.

If you previously downloaded a standalone `ai-conversation-studio-connected.html`
file — you don't need it anymore. The frontend now lives at `backend/frontend.html`
and is served automatically at `/`.

## Why you were seeing "backend not reached"

The earlier version had the frontend as a separate file you'd open directly
(`file://...`), pointing at `http://localhost:8000`. That only works if a backend
is *also* running on **your own machine** at that address — "localhost" always means
the computer the browser is running on, never a remote server. If you opened the
HTML file without first starting `uvicorn` yourself, there was nothing listening,
hence the error. Serving both from the same process (this version) removes that
whole class of mistake.

## What's real vs. mocked

- **Real**: the HTTP API, request/response validation, SQLite persistence,
  faithfulness/relevance/completeness scoring logic, governance policy engine,
  audit logging, analytics aggregation — all genuinely computed from stored data.
- **Mocked** (as scoped by the challenge): the LLM itself (`scoring.py:mock_generate`)
  and the knowledge sources (stored as plain text instead of a real vector DB /
  Confluence/SharePoint connector). Both are isolated behind small interfaces so
  they're the only things you'd swap for production use — see the design document.

## API docs

FastAPI auto-generates interactive docs once the server is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

All endpoints from the design doc's API section are implemented under `/api/v1`:
`/assistants`, `/knowledge-sources` (+ `/reindex`), `/conversations`, `/evaluations`,
`/feedback` (+ `/summary`), `/governance/policies` (+ `/audit-log`), `/analytics/*`.

## Reset the data

Delete `studio.db` and restart the server — it reseeds automatically on boot.