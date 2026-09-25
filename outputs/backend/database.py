"""Database layer with Supabase Postgres support and a local SQLite fallback."""
import sqlite3
import os
import random
import datetime as dt
import re
import logging

try:
    import psycopg
    from psycopg import errors as pg_errors
    from psycopg_pool import ConnectionPool
    from psycopg.rows import dict_row
except ImportError:  # SQLite-only local installs can still boot before dependency install.
    psycopg = None
    pg_errors = None
    ConnectionPool = None

DB_PATH = os.environ.get(
    "DB_PATH",
    "/tmp/studio.db" if os.environ.get("VERCEL") else os.path.join(os.path.dirname(__file__), "studio.db"),
)
SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL") or os.environ.get("DATABASE_URL")
USING_POSTGRES = bool(SUPABASE_DB_URL)
INTEGRITY_ERRORS = (sqlite3.IntegrityError, pg_errors.UniqueViolation) if pg_errors else (sqlite3.IntegrityError,)
logger = logging.getLogger(__name__)
POSTGRES_UNAVAILABLE = False
POSTGRES_POOL = None


class PostgresCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=()):
        self.cursor.execute(query.replace("?", "%s"), params)
        return self

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()


class PostgresConnection:
    def __init__(self, pool):
        if psycopg is None:
            raise RuntimeError("psycopg is required when SUPABASE_DB_URL is configured")
        self.pool = pool
        self.connection = pool.getconn()

    def execute(self, query, params=()):
        return self.connection.execute(query.replace("?", "%s"), params)

    def executescript(self, script):
        for statement in re.split(r";\s*(?:\n|$)", script):
            statement = statement.strip()
            if statement:
                self.connection.execute(statement)

    def cursor(self):
        return PostgresCursor(self.connection.cursor())

    def commit(self):
        self.connection.commit()

    def close(self):
        self.pool.putconn(self.connection)


def postgres_pool():
    global POSTGRES_POOL
    if POSTGRES_POOL is None:
        if ConnectionPool is None:
            raise RuntimeError("psycopg[pool] is required when SUPABASE_DB_URL is configured")
        POSTGRES_POOL = ConnectionPool(
            conninfo=SUPABASE_DB_URL,
            min_size=1,
            max_size=8,
            kwargs={"row_factory": dict_row, "connect_timeout": 8},
            open=True,
        )
    return POSTGRES_POOL

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
        dict(id="kb5", name="Security Policy — Endpoint and MFA", type="PDF policy doc",
            status="live", chunks=146,
            content=("Production access requires a company-managed device and multi-factor authentication. "
                    "Personal laptops may access approved low-risk tools only and may not access production systems. "
                    "Security incidents must be reported to the SOC within 30 minutes. "
                    "Privileged sessions require phishing-resistant MFA and are recorded.")),
        dict(id="kb6", name="Privacy and Data Handling Standard", type="PDF policy doc",
            status="live", chunks=203,
            content=("Customer personal data must be encrypted in transit and at rest. "
                    "Employees must not paste passwords, national IDs, payment card numbers, or private health information into an AI assistant. "
                    "Data retention is 30 days for conversation content unless a legal hold applies. "
                    "Privacy incidents must be reported to the Privacy Office within one business day.")),
        dict(id="kb7", name="Incident Response Playbook", type="Internal wiki",
            status="live", chunks=118,
            content=("A suspected security incident is triaged as P1 when production data or credentials may be exposed. "
                    "The incident commander opens a response channel, preserves evidence, and assigns a communications lead. "
                    "Customer notification requires Legal and Security approval. "
                    "Post-incident review is due within 10 business days.")),
        dict(id="kb8", name="Vendor Risk Management Standard", type="Confluence space",
            status="live", chunks=89,
            content=("New vendors handling confidential data require a security review before contracting. "
                    "Critical vendors are reassessed annually and must provide current compliance evidence. "
                    "Procurement may not approve a vendor with an unresolved critical finding without written risk acceptance.")),
        dict(id="kb9", name="Travel and Expense Policy 2026", type="DOCX",
            status="live", chunks=74,
            content=("Domestic travel must be booked through the approved travel portal. "
                    "Meals are reimbursable up to 75 dollars per day with an itemized receipt. "
                    "Manager approval is required before booking international travel. "
                    "Expense reports are due within 15 days of returning.")),
        dict(id="kb10", name="Business Continuity Plan", type="PDF policy doc",
            status="stale", chunks=132,
            content=("The recovery time objective for the customer API is four hours. "
                    "The recovery point objective is one hour. "
                    "Continuity exercises are performed twice per year and documented by the Resilience Owner.")),
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
    "Can I use my personal laptop to access production systems if I have MFA enabled?",
    "What information should never be pasted into the AI assistant?",
    "How quickly must a security incident be reported?",
    "When is a vendor security review required?",
    "What is the meal reimbursement limit?",
    "What is the customer API recovery time objective?",
    "Who approves customer notification after an incident?",
]

TEST_CASES = [
    ("kb1", "Can I get a refund on an annual contract after 20 days?"),
    ("kb1", "Are monthly contracts refundable after 14 days?"),
    ("kb2", "Does the platform support SAML and what is the Enterprise uptime SLA?"),
    ("kb3", "How much paid parental leave is available?"),
    ("kb4", "How many approvals are needed for production access?"),
    ("kb5", "Can I use my personal laptop to access production systems if I have MFA?"),
    ("kb5", "How quickly must a suspected security incident be reported?"),
    ("kb6", "Can I paste a customer national ID into the assistant?"),
    ("kb6", "How long is conversation content retained?"),
    ("kb7", "When does an incident require Legal approval for notification?"),
    ("kb8", "When is a vendor security review required?"),
    ("kb9", "What is the daily meal reimbursement limit?"),
    ("kb10", "What is the customer API recovery time objective?"),
]

FEEDBACK_COMMENTS = [
    "Accurate and cited the right clause.",
    "Missed the quarterly proration detail.",
    "Clear and fast, thanks.",
    "Slightly generic, wanted the exact SLA number.",
    "Correct but a bit verbose.",
]


def get_conn():
    global POSTGRES_UNAVAILABLE
    if USING_POSTGRES and not POSTGRES_UNAVAILABLE:
        try:
            return PostgresConnection(postgres_pool())
        except Exception as exc:
            logger.warning("Supabase PostgreSQL unavailable; using SQLite fallback: %s", exc)
            POSTGRES_UNAVAILABLE = True
    return sqlite_connection()


def sqlite_connection():
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

    policy_id = "SERIAL PRIMARY KEY" if USING_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    user_email = "TEXT NOT NULL UNIQUE" if USING_POSTGRES else "TEXT NOT NULL UNIQUE COLLATE NOCASE"
    schema = f"""
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
        review_status TEXT NOT NULL DEFAULT 'Pending',
        reviewed_by TEXT,
        reviewed_at TEXT,
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
        id {policy_id},
        name TEXT NOT NULL,
        "desc" TEXT NOT NULL,
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

    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email {user_email},
        role TEXT NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS auth_sessions (
        token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    conn.executescript(schema)
    conn.commit()

    if USING_POSTGRES and not POSTGRES_UNAVAILABLE:
        conversation_columns = {row["column_name"] for row in conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name='conversations'"
        ).fetchall()}
    else:
        conversation_columns = {row[1] for row in conn.execute("PRAGMA table_info(conversations)").fetchall()}
    for column, definition in (
        ("review_status", "TEXT NOT NULL DEFAULT 'Pending'"),
        ("reviewed_by", "TEXT"),
        ("reviewed_at", "TEXT"),
    ):
        if column not in conversation_columns:
            conn.execute(f"ALTER TABLE conversations ADD COLUMN {column} {definition}")
    conn.commit()

    # Keep existing demo installations manageable after introducing roles.
    admin_count = conn.execute("SELECT COUNT(*) AS count FROM users WHERE role='Platform Admin'").fetchone()["count"]
    if admin_count == 0:
        conn.execute(
            "UPDATE users SET role='Platform Admin' WHERE id=(SELECT id FROM users ORDER BY created_at LIMIT 1)"
        )
        conn.commit()

    source_count = conn.execute("SELECT COUNT(*) AS count FROM knowledge_sources").fetchone()["count"]
    conversation_count = conn.execute("SELECT COUNT(*) AS count FROM conversations").fetchone()["count"]
    if fresh or source_count < len(SOURCES_SEED) or conversation_count < 50:
        _seed(conn)
    conn.close()


def _rand_time_within(days_back):
    now = dt.datetime.utcnow()
    delta = dt.timedelta(seconds=random.uniform(0, days_back * 24 * 3600))
    return (now - delta).isoformat()


def _seed(conn):
    cur = conn.cursor()

    for s in SOURCES_SEED:
        existing = conn.execute("SELECT id FROM knowledge_sources WHERE id=?", (s["id"],)).fetchone()
        if not existing:
            cur.execute(
                "INSERT INTO knowledge_sources (id, name, type, status, chunks, content, updated_at) VALUES (?,?,?,?,?,?,?)",
                (s["id"], s["name"], s["type"], s["status"], s["chunks"], s["content"], _rand_time_within(2)),
            )

    for p in POLICIES_SEED:
        existing = conn.execute("SELECT id FROM policies WHERE name=?", (p["name"],)).fetchone()
        if not existing:
            cur.execute("INSERT INTO policies (name, \"desc\", enabled) VALUES (?,?,?)", (p["name"], p["desc"], p["enabled"]))

    import uuid
    from scoring import mock_generate  # local import to avoid circular import at module load

    existing_conversations = conn.execute("SELECT COUNT(*) AS count FROM conversations").fetchone()["count"]
    seed_cases = TEST_CASES + [random.choice(TEST_CASES) for _ in range(max(0, 60 - existing_conversations - len(TEST_CASES)))]
    for i, (source_id, case_prompt) in enumerate(seed_cases):
        assistant = random.choice(ASSISTANTS)
        src = next(source for source in SOURCES_SEED if source["id"] == source_id)
        prompt = case_prompt
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