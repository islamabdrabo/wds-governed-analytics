import sqlite3
from pathlib import Path

from cbi import apply_engine


def create_test_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE specialties (
            specialty_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            specialty_name TEXT NOT NULL
        );

        CREATE TABLE regions (
            region_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            region_name TEXT NOT NULL
        );

        CREATE TABLE workplaces (
            workplace_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            workplace_name TEXT NOT NULL
        );

        CREATE TABLE persons (
            person_id    TEXT PRIMARY KEY,
            specialty_id INTEGER,
            region_id    INTEGER,
            workplace_id INTEGER
        );

        CREATE TABLE cbi_batches (
            batch_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_name   TEXT,
            source_type  TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'PENDING',
            created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE workforce_staging (
            staging_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id       TEXT,
            action_type     TEXT NOT NULL,
            specialty_name  TEXT NOT NULL,
            region_name     TEXT NOT NULL,
            workplace_name  TEXT NOT NULL,
            source_note     TEXT,
            status          TEXT NOT NULL DEFAULT 'PENDING',
            created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            batch_id        INTEGER
        );

        CREATE TABLE workforce_audit_timeline (
            audit_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id        TEXT NOT NULL,
            batch_id         INTEGER NOT NULL,
            action_type      TEXT NOT NULL,
            change_summary   TEXT NOT NULL,
            applied_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()
    conn.close()


def test_apply_batch_handles_success_and_rejections(tmp_path, monkeypatch):
    db_path = tmp_path / "workforce_test.db"
    create_test_db(db_path)
    monkeypatch.setattr(apply_engine, "DB_PATH", db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Seed one existing person for UPDATE.
    cur.execute(
        "INSERT INTO specialties (specialty_name) VALUES (?)",
        ("OLD_SPECIALTY",),
    )
    old_specialty_id = cur.lastrowid
    cur.execute("INSERT INTO regions (region_name) VALUES (?)", ("OLD_REGION",))
    old_region_id = cur.lastrowid
    cur.execute("INSERT INTO workplaces (workplace_name) VALUES (?)", ("OLD_WORKPLACE",))
    old_workplace_id = cur.lastrowid
    cur.execute(
        """
        INSERT INTO persons (person_id, specialty_id, region_id, workplace_id)
        VALUES (?, ?, ?, ?)
        """,
        ("P100", old_specialty_id, old_region_id, old_workplace_id),
    )

    cur.execute(
        "INSERT INTO cbi_batches (batch_name, source_type, status) VALUES (?, ?, 'APPROVED')",
        ("TEST_BATCH", "MANUAL"),
    )
    batch_id = cur.lastrowid

    # Valid NEW.
    cur.execute(
        """
        INSERT INTO workforce_staging
        (person_id, action_type, specialty_name, region_name, workplace_name, status, batch_id)
        VALUES (?, 'NEW', ?, ?, ?, 'APPROVED', ?)
        """,
        ("P200", "NEW_SPECIALTY", "NEW_REGION", "NEW_WORKPLACE", batch_id),
    )

    # Valid UPDATE.
    cur.execute(
        """
        INSERT INTO workforce_staging
        (person_id, action_type, specialty_name, region_name, workplace_name, status, batch_id)
        VALUES (?, 'UPDATE', ?, ?, ?, 'APPROVED', ?)
        """,
        ("P100", "UPD_SPECIALTY", "UPD_REGION", "UPD_WORKPLACE", batch_id),
    )

    # Invalid UPDATE without person_id.
    cur.execute(
        """
        INSERT INTO workforce_staging
        (person_id, action_type, specialty_name, region_name, workplace_name, status, batch_id)
        VALUES (NULL, 'UPDATE', ?, ?, ?, 'APPROVED', ?)
        """,
        ("BAD_SPECIALTY", "BAD_REGION", "BAD_WORKPLACE", batch_id),
    )

    conn.commit()
    conn.close()

    result = apply_engine.apply_batch(batch_id)
    assert result["applied_rows"] == 2
    assert result["rejected_rows"] == 1
    assert result["batch_status"] == "PARTIAL_APPLIED"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    statuses = dict(
        cur.execute(
            """
            SELECT status, COUNT(*)
            FROM workforce_staging
            WHERE batch_id = ?
            GROUP BY status
            """,
            (batch_id,),
        ).fetchall()
    )
    assert statuses["APPLIED"] == 2
    assert statuses["REJECTED"] == 1

    # 2 successful actions -> 2 audit rows.
    audit_count = cur.execute(
        "SELECT COUNT(*) FROM workforce_audit_timeline WHERE batch_id = ?",
        (batch_id,),
    ).fetchone()[0]
    assert audit_count == 2

    # Ensure NEW row created and UPDATE row modified.
    new_person_exists = cur.execute(
        "SELECT COUNT(*) FROM persons WHERE person_id = 'P200'"
    ).fetchone()[0]
    assert new_person_exists == 1

    updated_person = cur.execute(
        """
        SELECT s.specialty_name, r.region_name, w.workplace_name
        FROM persons p
        LEFT JOIN specialties s ON p.specialty_id = s.specialty_id
        LEFT JOIN regions r ON p.region_id = r.region_id
        LEFT JOIN workplaces w ON p.workplace_id = w.workplace_id
        WHERE p.person_id = 'P100'
        """
    ).fetchone()
    assert updated_person == ("UPD_SPECIALTY", "UPD_REGION", "UPD_WORKPLACE")

    conn.close()


def test_apply_approved_changes_auto_creates_batch_for_unassigned_rows(tmp_path, monkeypatch):
    db_path = tmp_path / "workforce_test.db"
    create_test_db(db_path)
    monkeypatch.setattr(apply_engine, "DB_PATH", db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO workforce_staging
        (person_id, action_type, specialty_name, region_name, workplace_name, status, batch_id)
        VALUES (?, 'NEW', ?, ?, ?, 'APPROVED', NULL)
        """,
        ("P300", "AUTO_SPECIALTY", "AUTO_REGION", "AUTO_WORKPLACE"),
    )
    conn.commit()
    conn.close()

    results = apply_engine.apply_approved_changes()
    assert len(results) == 1
    assert results[0]["applied_rows"] == 1
    assert results[0]["batch_status"] == "APPLIED"

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    batch_count = cur.execute("SELECT COUNT(*) FROM cbi_batches").fetchone()[0]
    assert batch_count == 1
    conn.close()
