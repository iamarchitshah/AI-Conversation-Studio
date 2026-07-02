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
