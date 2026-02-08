import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "workforce.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
DROP VIEW IF EXISTS v_workforce_by_specialty_canonical;

CREATE VIEW v_workforce_by_specialty_canonical AS
SELECT
    COALESCE(a.canonical_name, s.specialty_name) AS specialty,
    COUNT(p.person_id) AS workforce_count
FROM persons p
JOIN specialties s ON p.specialty_id = s.specialty_id
LEFT JOIN specialty_aliases a
       ON a.alias_name = s.specialty_name
GROUP BY COALESCE(a.canonical_name, s.specialty_name)
ORDER BY workforce_count DESC;
""")

conn.commit()
conn.close()

print("[OK] Canonical specialty view created")
