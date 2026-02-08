import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "workforce.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
-- Indexes for faster aggregation and joins
CREATE INDEX IF NOT EXISTS idx_persons_specialty
    ON persons (specialty_id);

CREATE INDEX IF NOT EXISTS idx_persons_region
    ON persons (region_id);

CREATE INDEX IF NOT EXISTS idx_persons_workplace
    ON persons (workplace_id);
""")

conn.commit()
conn.close()

print("[OK] Indexes created successfully")
