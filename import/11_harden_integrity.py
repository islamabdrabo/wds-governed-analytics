import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "workforce.db"


def create_unique_index(cur: sqlite3.Cursor, sql: str, label: str) -> None:
    try:
        cur.execute(sql)
        print(f"[OK] {label}")
    except sqlite3.IntegrityError as exc:
        print(f"[WARN] Skipped {label}: {exc}")


conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

create_unique_index(
    cur,
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_specialties_name_unique ON specialties (specialty_name COLLATE NOCASE)",
    "specialties unique index",
)
create_unique_index(
    cur,
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_regions_name_unique ON regions (region_name COLLATE NOCASE)",
    "regions unique index",
)
create_unique_index(
    cur,
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_workplaces_name_unique ON workplaces (workplace_name COLLATE NOCASE)",
    "workplaces unique index",
)

cur.executescript(
    """
    CREATE INDEX IF NOT EXISTS idx_staging_batch_status
    ON workforce_staging(batch_id, status);

    CREATE INDEX IF NOT EXISTS idx_batches_status
    ON cbi_batches(status);

    CREATE INDEX IF NOT EXISTS idx_audit_batch
    ON workforce_audit_timeline(batch_id);
    """
)

conn.commit()
conn.close()

print("[DONE] Integrity hardening completed")
