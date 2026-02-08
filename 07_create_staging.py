import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "workforce.db"


def table_has_column(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row[1] == column_name for row in rows)


SQL = """
CREATE TABLE IF NOT EXISTS cbi_batches (
    batch_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_name   TEXT,
    source_type  TEXT NOT NULL CHECK (
        source_type IN ('FILE_UPLOAD', 'SYSTEM_AUTO', 'MANUAL')
    ),
    status       TEXT NOT NULL DEFAULT 'PENDING' CHECK (
        status IN ('PENDING', 'APPROVED', 'REJECTED', 'APPLIED', 'PARTIAL_APPLIED')
    ),
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workforce_staging (
    staging_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id       TEXT,
    action_type     TEXT NOT NULL CHECK (action_type IN ('NEW', 'UPDATE')),
    specialty_name  TEXT NOT NULL CHECK (LENGTH(TRIM(specialty_name)) > 0),
    region_name     TEXT NOT NULL CHECK (LENGTH(TRIM(region_name)) > 0),
    workplace_name  TEXT NOT NULL CHECK (LENGTH(TRIM(workplace_name)) > 0),
    source_note     TEXT,
    status          TEXT NOT NULL DEFAULT 'PENDING' CHECK (
        status IN ('PENDING', 'APPROVED', 'REJECTED', 'APPLIED')
    ),
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    batch_id        INTEGER,
    FOREIGN KEY (batch_id) REFERENCES cbi_batches(batch_id)
);

CREATE TABLE IF NOT EXISTS workforce_audit_timeline (
    audit_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id        TEXT NOT NULL CHECK (LENGTH(TRIM(person_id)) > 0),
    batch_id         INTEGER NOT NULL,
    action_type      TEXT NOT NULL CHECK (action_type IN ('NEW', 'UPDATE')),
    change_summary   TEXT NOT NULL CHECK (LENGTH(TRIM(change_summary)) > 0),
    applied_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES cbi_batches(batch_id)
);
"""


TRIGGERS = """
CREATE TRIGGER IF NOT EXISTS trg_staging_insert_validate
BEFORE INSERT ON workforce_staging
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN UPPER(NEW.action_type) NOT IN ('NEW', 'UPDATE')
        THEN RAISE(ABORT, 'Invalid action_type in workforce_staging')
    END;
    SELECT CASE
        WHEN UPPER(NEW.status) NOT IN ('PENDING', 'APPROVED', 'REJECTED', 'APPLIED')
        THEN RAISE(ABORT, 'Invalid status in workforce_staging')
    END;
    SELECT CASE
        WHEN UPPER(NEW.action_type) = 'UPDATE'
             AND (NEW.person_id IS NULL OR LENGTH(TRIM(NEW.person_id)) = 0)
        THEN RAISE(ABORT, 'UPDATE staging records require person_id')
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_staging_update_validate
BEFORE UPDATE ON workforce_staging
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN UPPER(NEW.action_type) NOT IN ('NEW', 'UPDATE')
        THEN RAISE(ABORT, 'Invalid action_type in workforce_staging')
    END;
    SELECT CASE
        WHEN UPPER(NEW.status) NOT IN ('PENDING', 'APPROVED', 'REJECTED', 'APPLIED')
        THEN RAISE(ABORT, 'Invalid status in workforce_staging')
    END;
    SELECT CASE
        WHEN UPPER(NEW.action_type) = 'UPDATE'
             AND (NEW.person_id IS NULL OR LENGTH(TRIM(NEW.person_id)) = 0)
        THEN RAISE(ABORT, 'UPDATE staging records require person_id')
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_batches_status_validate_insert
BEFORE INSERT ON cbi_batches
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN UPPER(NEW.status) NOT IN ('PENDING', 'APPROVED', 'REJECTED', 'APPLIED', 'PARTIAL_APPLIED')
        THEN RAISE(ABORT, 'Invalid status in cbi_batches')
    END;
END;

CREATE TRIGGER IF NOT EXISTS trg_batches_status_validate_update
BEFORE UPDATE ON cbi_batches
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN UPPER(NEW.status) NOT IN ('PENDING', 'APPROVED', 'REJECTED', 'APPLIED', 'PARTIAL_APPLIED')
        THEN RAISE(ABORT, 'Invalid status in cbi_batches')
    END;
END;
"""


conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.executescript(SQL)

# Upgrade path: ensure legacy staging tables include batch_id.
if not table_has_column(conn, "workforce_staging", "batch_id"):
    cur.execute("ALTER TABLE workforce_staging ADD COLUMN batch_id INTEGER")

cur.executescript(
    """
    CREATE INDEX IF NOT EXISTS idx_staging_status
    ON workforce_staging(status);

    CREATE INDEX IF NOT EXISTS idx_staging_batch_id
    ON workforce_staging(batch_id);

    CREATE INDEX IF NOT EXISTS idx_staging_batch_status
    ON workforce_staging(batch_id, status);

    CREATE INDEX IF NOT EXISTS idx_batches_status
    ON cbi_batches(status);

    CREATE INDEX IF NOT EXISTS idx_audit_batch
    ON workforce_audit_timeline(batch_id);
    """
)

cur.executescript(TRIGGERS)

conn.commit()
conn.close()

print("[OK] Staging, batches, and audit tables are ready with constraints")
