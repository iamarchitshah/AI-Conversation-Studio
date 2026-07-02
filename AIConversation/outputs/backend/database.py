"""
SQLite data layer for the AI Conversation Studio backend.
Kept as plain sqlite3 (no ORM) so the schema is easy to read end-to-end
for a 48-hour build. Swap for Postgres + SQLAlchemy for production.
"""
import sqlite3
import os
import random
import datetime as dt

DB_PATH = os.path.join(os.path.dirname(__file__), "studio.db")

ASSISTANTS = ["Support Copilot", "Sales Assistant", "HR Helpdesk", "IT Service Bot"]

SOURCES_SEED = [
    dict(id="kb1", name="Enterprise Contract Terms v4.2", type="PDF policy doc",
         status="live", chunks=184,
         content=("Enterprise annual contracts are refundable within 30 days of signing "
                   "if usage is under 5 percent. After 30 days, refunds are prorated only "
                   "for unused whole quarters and require VP approval. Monthly contracts "
                   "are non-refundable after the first 14 days.")),
    dict(id="kb2", name="Product FAQ — Platform", type="Confluence space",
         status="live", chunks=412,
         content=("The platform supports SSO via SAML and OIDC. Data is encrypted at rest "
                   "with AES-256 and in transit with TLS 1.3. Uptime SLA is 99.9 percent for "
                   "Enterprise tier. Support response time is 4 business hours for Enterprise.")),
    dict(id="kb3", name="HR Policy Handbook 2026", type="DOCX",
         status="live", chunks=97,
         content=("Employees accrue 1.5 days of PTO per month, capped at 24 days per year. "
                   "Parental leave is 16 weeks paid. Remote work requires manager approval "
                   "and is reviewed quarterly.")),
    dict(id="kb4", name="IT Runbook — Access Requests", type="Internal wiki",
         status="stale", chunks=63,
         content=("Access requests for production systems require two approvals and are "
                   "provisioned within 1 business day. VPN credentials rotate every 90 days.")),
]

POLICIES_SEED = [
    dict(name="PII redaction", desc="Mask emails, phone numbers, national IDs, and card numbers before responses reach the end user.", enabled=1),
    dict(name="Banned topic filter", desc="Block responses touching legal advice, medical diagnosis, or unreleased financial results.", enabled=1),
    dict(name="Faithfulness threshold", desc="Escalate to human review if faithfulness score falls below 70%.", enabled=1),
    dict(name="Response length cap", desc="Flag responses exceeding 400 words for regulated assistants (HR, Legal).", enabled=0),
    dict(name="Source freshness check", desc="Warn when a response is grounded in a knowledge source untouched for 30+ days.", enabled=1),
]

SAMPLE_PROMPTS = [
    "What's the SSO setup process?",
    "Can I get a refund on my annual plan?",
    "How many PTO days do I accrue?",
    "What's the uptime SLA?",
    "How do I request VPN access?",
    "What's our parental leave policy?",
]

FEEDBACK_COMMENTS = [
    "Accurate and cited the right clause.",
    "Missed the quarterly proration detail.",
    "Clear and fast, thanks.",
    "Slightly generic, wanted the exact SLA number.",
    "Correct but a bit verbose.",
]


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(reset: bool = False):
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    fresh = not os.path.exists(DB_PATH)
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS knowledge_sources (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'live',
        chunks INTEGER NOT NULL DEFAULT 0,
        content TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS conversations (
        id TEXT PRIMARY KEY,
        assistant TEXT NOT NULL,
        knowledge_source_id TEXT,
        prompt TEXT NOT NULL,
        response_html TEXT NOT NULL,
        faithfulness INTEGER NOT NULL,
        relevance INTEGER NOT NULL,
        completeness INTEGER NOT NULL,
        flagged INTEGER NOT NULL DEFAULT 0,
        latency_ms INTEGER NOT NULL,
        tokens INTEGER NOT NULL,
        explanation TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (knowledge_source_id) REFERENCES knowledge_sources(id)
    );

    CREATE TABLE IF NOT EXISTS feedback (
        id TEXT PRIMARY KEY,
        conversation_id TEXT,
        assistant TEXT NOT NULL,
        prompt TEXT NOT NULL,
        rating INTEGER NOT NULL,
        comment TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
    );

    CREATE TABLE IF NOT EXISTS policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        desc TEXT NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS audit_log (
        id TEXT PRIMARY KEY,
        assistant TEXT NOT NULL,
        policy TEXT NOT NULL,
        action TEXT NOT NULL,
        reviewer TEXT,
        created_at TEXT NOT NULL
    );
    """)
    conn.commit()

    if fresh:
        _seed(conn)
    conn.close()


def _rand_time_within(days_back):
    now = dt.datetime.utcnow()
    delta = dt.timedelta(seconds=random.uniform(0, days_back * 24 * 3600))
    return (now - delta).isoformat()


def _seed(conn):
    cur = conn.cursor()

    for s in SOURCES_SEED:
        cur.execute(
            "INSERT INTO knowledge_sources (id, name, type, status, chunks, content, updated_at) VALUES (?,?,?,?,?,?,?)",
            (s["id"], s["name"], s["type"], s["status"], s["chunks"], s["content"], _rand_time_within(2)),
        )

    for p in POLICIES_SEED:
        cur.execute("INSERT INTO policies (name, desc, enabled) VALUES (?,?,?)", (p["name"], p["desc"], p["enabled"]))

    import uuid
    from scoring import mock_generate  # local import to avoid circular import at module load

    for i in range(40):
        assistant = random.choice(ASSISTANTS)
        src = random.choice(SOURCES_SEED)
        prompt = random.choice(SAMPLE_PROMPTS)
        result = mock_generate(prompt, src["name"], src["content"])
        conv_id = str(uuid.uuid4())
        created = _rand_time_within(14)
        cur.execute(
            """INSERT INTO conversations
               (id, assistant, knowledge_source_id, prompt, response_html, faithfulness, relevance,
                completeness, flagged, latency_ms, tokens, explanation, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (conv_id, assistant, src["id"], prompt, result["html"], result["faith"], result["rel"],
             result["comp"], 1 if result["faith"] < 70 else 0, result["latency"], result["tokens"],
             result["explain"], created),
        )
        if random.random() > 0.4:
            cur.execute(
                "INSERT INTO feedback (id, conversation_id, assistant, prompt, rating, comment, created_at) VALUES (?,?,?,?,?,?,?)",
                (str(uuid.uuid4()), conv_id, assistant, prompt, 1 if random.random() > 0.25 else 0,
                 random.choice(FEEDBACK_COMMENTS), created),
            )
        if result["faith"] < 70 and random.random() > 0.5:
            cur.execute(
                "INSERT INTO audit_log (id, assistant, policy, action, reviewer, created_at) VALUES (?,?,?,?,?,?)",
                (str(uuid.uuid4()), assistant, random.choice(["Faithfulness threshold", "PII redaction", "Source freshness check"]),
                 random.choice(["Escalated for review", "Response withheld", "Redacted 1 field"]),
                 random.choice(["A. Mehta", "—", "S. Rao", "Auto-governed"]), created),
            )

    conn.commit()