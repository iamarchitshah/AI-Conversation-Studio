# AI Conversation Studio — Backend

A real FastAPI + SQLite backend implementing the API design from the challenge doc,
now serving the frontend directly so there is exactly **one thing to start and one
URL to open**.

## Run it (3 steps)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000
```

Then open **http://localhost:8000** in your browser. That's it — no separate HTML
file to open, no CORS setup, no host/port mismatch. The page is served by the same
process as the API, so `connStatus` in the left nav should immediately read
"● connected to http://localhost:8000/api/v1".

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