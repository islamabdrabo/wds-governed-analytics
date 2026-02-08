import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "workforce.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
-- =========================
-- View 1: Count by Specialty
-- =========================
DROP VIEW IF EXISTS v_workforce_by_specialty;
CREATE VIEW v_workforce_by_specialty AS
SELECT
    s.specialty_name   AS specialty,
    COUNT(p.person_id) AS workforce_count
FROM persons p
JOIN specialties s ON p.specialty_id = s.specialty_id
GROUP BY s.specialty_name;


-- =========================
-- View 2: Count by Region
-- =========================
DROP VIEW IF EXISTS v_workforce_by_region;
CREATE VIEW v_workforce_by_region AS
SELECT
    r.region_name      AS region,
    COUNT(p.person_id) AS workforce_count
FROM persons p
JOIN regions r ON p.region_id = r.region_id
GROUP BY r.region_name;


-- =========================================
-- View 3: Count by Region + Workplace
-- =========================================
DROP VIEW IF EXISTS v_workforce_by_region_workplace;
CREATE VIEW v_workforce_by_region_workplace AS
SELECT
    r.region_name       AS region,
    w.workplace_name    AS workplace,
    COUNT(p.person_id)  AS workforce_count
FROM persons p
JOIN regions r   ON p.region_id = r.region_id
JOIN workplaces w ON p.workplace_id = w.workplace_id
GROUP BY r.region_name, w.workplace_name;


-- ==================================================
-- View 4: Canonical Workforce Base (for reuse)
-- ==================================================
DROP VIEW IF EXISTS v_workforce_base;
CREATE VIEW v_workforce_base AS
SELECT
    p.person_id,
    s.specialty_name,
    r.region_name,
    w.workplace_name
FROM persons p
LEFT JOIN specialties s ON p.specialty_id = s.specialty_id
LEFT JOIN regions r     ON p.region_id = r.region_id
LEFT JOIN workplaces w ON p.workplace_id = w.workplace_id;
""")

conn.commit()
conn.close()

print("[OK] Workforce views created successfully")
