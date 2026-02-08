import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "workforce.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS specialty_aliases;

CREATE TABLE specialty_aliases (
    alias_name      TEXT PRIMARY KEY,
    canonical_name  TEXT NOT NULL
);
""")

conn.commit()
conn.close()

print("[OK] specialty_aliases table created")
