"""
AI Conversation Studio — backend API
Run with:  uvicorn main:app --reload --port 8000
Docs at:   http://localhost:8000/docs
"""
import uuid
import datetime as dt
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import database as db
from scoring import mock_generate

app = FastAPI(title="AI Conversation Studio API", version="1.0")

# CORS stays wide-open — harmless for local/demo use, and keeps things working
# even if someone opens the frontend from a different origin than the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()

ASSISTANTS = db.ASSISTANTS

FRONTEND_FILE = Path(__file__).parent / "frontend.html"

@app.get("/")
def serve_frontend():
    """Serves the Studio UI from the same server/origin as the API, so there is
    exactly one thing to start and one URL to open — no separate file, no
    host/port mismatch, no CORS surprises."""
    return FileResponse(FRONTEND_FILE)

# ---------------------------------------------------------------- schemas
class RunPromptRequest(BaseModel):
    assistantId: str
    knowledgeSourceId: str
    prompt: str

class NewSourceRequest(BaseModel):
    name: str
    type: str = "Uploaded doc"
    content: str = ""

class FeedbackRequest(BaseModel):
    conversationId: Optional[str] = None
    assistant: str
    prompt: str
    rating: bool
    comment: Optional[str] = ""

class PolicyPatch(BaseModel):
    enabled: Optional[bool] = None
    desc: Optional[str] = None


def now_iso():
    return dt.datetime.utcnow().isoformat()


# ================================================================== CONVERSATIONS
@app.post("/api/v1/conversations")
def run_prompt(req: RunPromptRequest):
    conn = db.get_conn()
    src = conn.execute("SELECT * FROM knowledge_sources WHERE id=?", (req.knowledgeSourceId,)).fetchone()
    if not src:
        conn.close()
        raise HTTPException(404, "Unknown knowledgeSourceId")

    result = mock_generate(req.prompt, src["name"], src["content"])
    conv_id = str(uuid.uuid4())
    flagged = 1 if result["faith"] < 70 else 0
    created = now_iso()

    conn.execute(
        """INSERT INTO conversations
           (id, assistant, knowledge_source_id, prompt, response_html, faithfulness, relevance,
            completeness, flagged, latency_ms, tokens, explanation, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (conv_id, req.assistantId, req.knowledgeSourceId, req.prompt, result["html"], result["faith"],
         result["rel"], result["comp"], flagged, result["latency"], result["tokens"], result["explain"], created),
    )

    # Governance side-effect: escalate if a currently-enabled faithfulness policy fires.
    policy = conn.execute("SELECT * FROM policies WHERE name='Faithfulness threshold'").fetchone()
    if flagged and policy and policy["enabled"]:
        conn.execute(
            "INSERT INTO audit_log (id, assistant, policy, action, reviewer, created_at) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4()), req.assistantId, "Faithfulness threshold", "Escalated for review", "—", created),
        )

    conn.commit()
    conn.close()

    return {
        "conversationId": conv_id,
        "response": result["html"],
        "citations": result["spans"],
        "evaluation": {
            "faithfulness": result["faith"],
            "relevance": result["rel"],
            "completeness": result["comp"],
            "flagged": bool(flagged),
            "explanation": result["explain"],
        },
        "latencyMs": result["latency"],
        "tokens": result["tokens"],
        "createdAt": created,
    }


@app.get("/api/v1/conversations")
def list_conversations(assistant: Optional[str] = None, flagged: Optional[bool] = None,
                        page: int = 1, pageSize: int = 50):
    conn = db.get_conn()
    q = "SELECT * FROM conversations WHERE 1=1"
    params = []
    if assistant and assistant != "All assistants":
        q += " AND assistant=?"
        params.append(assistant)
    if flagged is not None:
        q += " AND flagged=?"
        params.append(1 if flagged else 0)
    q += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params += [pageSize, (page - 1) * pageSize]
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Not found")
    return dict(row)


# ================================================================== KNOWLEDGE SOURCES
@app.get("/api/v1/knowledge-sources")
def list_sources():
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM knowledge_sources ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/v1/knowledge-sources")
def add_source(req: NewSourceRequest):
    conn = db.get_conn()
    sid = "kb-" + str(uuid.uuid4())[:8]
    content = req.content or f"Simulated content chunk for {req.name}."
    conn.execute(
        "INSERT INTO knowledge_sources (id, name, type, status, chunks, content, updated_at) VALUES (?,?,?,?,?,?,?)",
        (sid, req.name, req.type, "live", max(10, len(content) // 8), content, now_iso()),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM knowledge_sources WHERE id=?", (sid,)).fetchone()
    conn.close()
    return dict(row)


@app.post("/api/v1/knowledge-sources/{source_id}/reindex")
def reindex_source(source_id: str):
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM knowledge_sources WHERE id=?", (source_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Not found")
    conn.execute("UPDATE knowledge_sources SET status='live', updated_at=? WHERE id=?", (now_iso(), source_id))
    conn.commit()
    row = conn.execute("SELECT * FROM knowledge_sources WHERE id=?", (source_id,)).fetchone()
    conn.close()
    return dict(row)


@app.delete("/api/v1/knowledge-sources/{source_id}")
def delete_source(source_id: str):
    conn = db.get_conn()
    conn.execute("DELETE FROM knowledge_sources WHERE id=?", (source_id,))
    conn.commit()
    conn.close()
    return {"deleted": source_id}


# ================================================================== EVALUATIONS
@app.get("/api/v1/evaluations")
def list_evaluations(assistant: Optional[str] = None, flagged: Optional[bool] = None,
                      minScore: Optional[int] = None, page: int = 1, pageSize: int = 60):
    conn = db.get_conn()
    q = "SELECT id as conversationId, assistant, prompt, faithfulness, relevance, completeness, flagged, created_at FROM conversations WHERE 1=1"
    params = []
    if assistant and assistant != "All assistants":
        q += " AND assistant=?"
        params.append(assistant)
    if flagged is not None:
        q += " AND flagged=?"
        params.append(1 if flagged else 0)
    if minScore is not None:
        q += " AND faithfulness>=?"
        params.append(minScore)
    q += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params += [pageSize, (page - 1) * pageSize]
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/evaluations/{conversation_id}")
def get_evaluation(conversation_id: str):
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "Not found")
    return dict(row)


@app.post("/api/v1/evaluations/{conversation_id}/rescore")
def rescore(conversation_id: str):
    conn = db.get_conn()
    conv = conn.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
    if not conv:
        conn.close()
        raise HTTPException(404, "Not found")
    src = conn.execute("SELECT * FROM knowledge_sources WHERE id=?", (conv["knowledge_source_id"],)).fetchone()
    result = mock_generate(conv["prompt"], src["name"], src["content"])
    flagged = 1 if result["faith"] < 70 else 0
    conn.execute(
        """UPDATE conversations SET response_html=?, faithfulness=?, relevance=?, completeness=?,
           flagged=?, explanation=? WHERE id=?""",
        (result["html"], result["faith"], result["rel"], result["comp"], flagged, result["explain"], conversation_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
    conn.close()
    return dict(row)


# ================================================================== FEEDBACK
@app.post("/api/v1/feedback")
def submit_feedback(req: FeedbackRequest):
    conn = db.get_conn()
    fid = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO feedback (id, conversation_id, assistant, prompt, rating, comment, created_at) VALUES (?,?,?,?,?,?,?)",
        (fid, req.conversationId, req.assistant, req.prompt, 1 if req.rating else 0, req.comment, now_iso()),
    )
    conn.commit()
    conn.close()
    return {"id": fid, "status": "recorded"}


@app.get("/api/v1/feedback")
def list_feedback(assistant: Optional[str] = None, rating: Optional[bool] = None, page: int = 1, pageSize: int = 60):
    conn = db.get_conn()
    q = "SELECT * FROM feedback WHERE 1=1"
    params = []
    if assistant and assistant != "All assistants":
        q += " AND assistant=?"
        params.append(assistant)
    if rating is not None:
        q += " AND rating=?"
        params.append(1 if rating else 0)
    q += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params += [pageSize, (page - 1) * pageSize]
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/feedback/summary")
def feedback_summary(assistant: Optional[str] = None):
    conn = db.get_conn()
    q = "SELECT rating FROM feedback WHERE 1=1"
    params = []
    if assistant and assistant != "All assistants":
        q += " AND assistant=?"
        params.append(assistant)
    rows = conn.execute(q, params).fetchall()
    conn.close()
    total = len(rows)
    positive = sum(1 for r in rows if r["rating"])
    return {
        "total": total,
        "positive": positive,
        "negative": total - positive,
        "satisfactionPct": round(100 * positive / total) if total else 0,
    }


# ================================================================== GOVERNANCE
@app.get("/api/v1/governance/policies")
def list_policies():
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM policies ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.patch("/api/v1/governance/policies/{policy_id}")
def patch_policy(policy_id: int, patch: PolicyPatch):
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM policies WHERE id=?", (policy_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "Not found")
    enabled = row["enabled"] if patch.enabled is None else (1 if patch.enabled else 0)
    desc = row["desc"] if patch.desc is None else patch.desc
    conn.execute("UPDATE policies SET enabled=?, desc=? WHERE id=?", (enabled, desc, policy_id))
    conn.commit()
    row = conn.execute("SELECT * FROM policies WHERE id=?", (policy_id,)).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/v1/governance/audit-log")
def audit_log(assistant: Optional[str] = None, action: Optional[str] = None, page: int = 1, pageSize: int = 60):
    conn = db.get_conn()
    q = "SELECT * FROM audit_log WHERE 1=1"
    params = []
    if assistant and assistant != "All assistants":
        q += " AND assistant=?"
        params.append(assistant)
    if action:
        q += " AND action=?"
        params.append(action)
    q += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params += [pageSize, (page - 1) * pageSize]
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ================================================================== ANALYTICS
@app.get("/api/v1/analytics/kpis")
def kpis(assistantId: Optional[str] = Query(None)):
    conn = db.get_conn()
    q = "SELECT * FROM conversations WHERE 1=1"
    params = []
    if assistantId and assistantId != "All assistants":
        q += " AND assistant=?"
        params.append(assistantId)
    convs = conn.execute(q, params).fetchall()

    fq = "SELECT * FROM feedback WHERE 1=1"
    fparams = []
    if assistantId and assistantId != "All assistants":
        fq += " AND assistant=?"
        fparams.append(assistantId)
    fbs = conn.execute(fq, fparams).fetchall()
    conn.close()

    n = len(convs)
    avg_faith = round(sum(c["faithfulness"] for c in convs) / n) if n else 0
    hallu_rate = round(100 * sum(1 for c in convs if c["flagged"]) / n) if n else 0
    pos = sum(1 for f in fbs if f["rating"])
    pos_rate = round(100 * pos / len(fbs)) if fbs else 0

    return {
        "conversationsLogged": n,
        "avgFaithfulness": avg_faith,
        "hallucinationRate": hallu_rate,
        "positiveFeedbackPct": pos_rate,
        "assistantCount": len(ASSISTANTS),
    }


@app.get("/api/v1/analytics/trend")
def trend(metric: str = "faithfulness", days: int = 14):
    conn = db.get_conn()
    rows = conn.execute("SELECT created_at, faithfulness FROM conversations ORDER BY created_at").fetchall()
    conn.close()
    buckets = {}
    for r in rows:
        day = r["created_at"][:10]
        buckets.setdefault(day, []).append(r["faithfulness"])
    days_sorted = sorted(buckets.keys())[-days:]
    return {
        "labels": days_sorted,
        "values": [round(sum(buckets[d]) / len(buckets[d])) for d in days_sorted],
    }


@app.get("/api/v1/analytics/by-assistant")
def by_assistant(metric: str = "hallucinationRate"):
    conn = db.get_conn()
    out = []
    for a in ASSISTANTS:
        rows = conn.execute("SELECT faithfulness, flagged FROM conversations WHERE assistant=?", (a,)).fetchall()
        n = len(rows)
        if metric == "hallucinationRate":
            val = round(100 * sum(1 for r in rows if r["flagged"]) / n) if n else 0
        else:
            val = round(sum(r["faithfulness"] for r in rows) / n) if n else 0
        out.append({"assistant": a, "value": val, "sampleSize": n})
    conn.close()
    return out


@app.get("/api/v1/analytics/by-source")
def by_source(metric: str = "volume"):
    conn = db.get_conn()
    rows = conn.execute(
        """SELECT ks.name as source, COUNT(c.id) as volume
           FROM knowledge_sources ks LEFT JOIN conversations c ON c.knowledge_source_id = ks.id
           GROUP BY ks.id ORDER BY ks.name"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/v1/assistants")
def list_assistants():
    return ASSISTANTS


@app.get("/health")
def health():
    return {"status": "ok"}