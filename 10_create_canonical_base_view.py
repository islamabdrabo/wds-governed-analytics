import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "workforce.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
DROP VIEW IF EXISTS v_workforce_base_canonical;

CREATE VIEW v_workforce_base_canonical AS
SELECT
    p.person_id,
    COALESCE(a.canonical_name, s.specialty_name) AS specialty_name,
    r.region_name,
    w.workplace_name
FROM persons p
JOIN specialties s ON p.specialty_id = s.specialty_id
LEFT JOIN specialty_aliases a
       ON a.alias_name = s.specialty_name
LEFT JOIN regions r     ON p.region_id = r.region_id
LEFT JOIN workplaces w ON p.workplace_id = w.workplace_id;
""")

conn.commit()
conn.close()

print("[OK] Canonical base view created")
