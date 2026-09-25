"""Initialize the configured database and load the demo evaluation dataset.

SQLite is used when SUPABASE_DB_URL is absent. Set SUPABASE_DB_URL to a
Supabase PostgreSQL URI to initialize the shared project database instead.
"""
import sys
from pathlib import Path

backend = Path(__file__).resolve().parents[1] / "outputs" / "backend"
sys.path.insert(0, str(backend))

import database as db


db.init_db()
conn = db.get_conn()
for table in ("knowledge_sources", "conversations", "feedback", "policies", "audit_log"):
    row = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()
    print(f"{table}: {row['count']}")
conn.close()
print("Database initialization and idempotent seed completed.")
