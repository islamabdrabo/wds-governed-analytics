from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

from config.paths import DB_PATH


DIMENSIONS = {
    "specialty": ("specialties", "specialty_id", "specialty_name"),
    "region": ("regions", "region_id", "region_name"),
    "workplace": ("workplaces", "workplace_id", "workplace_name"),
}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def normalize_text(value: object) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    return text


def write_audit_entry(
    conn: sqlite3.Connection,
    person_id: str,
    batch_id: int,
    action_type: str,
    summary: str,
) -> None:
    conn.execute(
        """
        INSERT INTO workforce_audit_timeline
        (person_id, batch_id, action_type, change_summary)
        VALUES (?, ?, ?, ?)
        """,
        (person_id, batch_id, action_type, summary),
    )


def get_or_create_dimension_id(
    cur: sqlite3.Cursor,
    table_name: str,
    id_col: str,
    name_col: str,
    name_value: object,
) -> int:
    normalized = normalize_text(name_value)
    if not normalized:
        raise ValueError(f"Missing value for {name_col}")

    row = cur.execute(
        f"SELECT {id_col} FROM {table_name} WHERE {name_col} = ?",
        (normalized,),
    ).fetchone()
    if row:
        return int(row[0])

    cur.execute(
        f"INSERT INTO {table_name} ({name_col}) VALUES (?)",
        (normalized,),
    )
    return int(cur.lastrowid)


def get_dimension_name(
    cur: sqlite3.Cursor,
    table_name: str,
    id_col: str,
    name_col: str,
    row_id: Optional[int],
) -> Optional[str]:
    if row_id is None:
        return None
    row = cur.execute(
        f"SELECT {name_col} FROM {table_name} WHERE {id_col} = ?",
        (row_id,),
    ).fetchone()
    return row[0] if row else None


def append_source_note(cur: sqlite3.Cursor, staging_id: int, message: str) -> None:
    cur.execute(
        """
        UPDATE workforce_staging
        SET source_note = CASE
            WHEN source_note IS NULL OR TRIM(source_note) = '' THEN ?
            ELSE source_note || ' | ' || ?
        END
        WHERE staging_id = ?
        """,
        (message, message, staging_id),
    )


def apply_batch(batch_id: int) -> Dict[str, int]:
    conn = get_conn()
    cur = conn.cursor()

    try:
        rows = cur.execute(
            """
            SELECT
                staging_id,
                person_id,
                action_type,
                specialty_name,
                region_name,
                workplace_name
            FROM workforce_staging
            WHERE batch_id = ?
              AND status = 'APPROVED'
            ORDER BY staging_id
            """,
            (batch_id,),
        ).fetchall()

        if not rows:
            return {
                "batch_id": batch_id,
                "total_rows": 0,
                "applied_rows": 0,
                "rejected_rows": 0,
                "batch_status": "NOOP",
            }

        applied_rows = 0
        rejected_rows = 0

        for row in rows:
            (
                staging_id,
                person_id_raw,
                action_type_raw,
                specialty_name,
                region_name,
                workplace_name,
            ) = row

            person_id = normalize_text(person_id_raw)
            action_type = (normalize_text(action_type_raw) or "").upper()

            try:
                specialty_id = get_or_create_dimension_id(
                    cur, *DIMENSIONS["specialty"], specialty_name
                )
                region_id = get_or_create_dimension_id(
                    cur, *DIMENSIONS["region"], region_name
                )
                workplace_id = get_or_create_dimension_id(
                    cur, *DIMENSIONS["workplace"], workplace_name
                )

                if action_type == "NEW":
                    if not person_id:
                        raise ValueError("NEW record is missing person_id")

                    exists = cur.execute(
                        "SELECT 1 FROM persons WHERE person_id = ?",
                        (person_id,),
                    ).fetchone()
                    if exists:
                        raise ValueError("person_id already exists for NEW action")

                    cur.execute(
                        """
                        INSERT INTO persons
                        (person_id, specialty_id, region_id, workplace_id)
                        VALUES (?, ?, ?, ?)
                        """,
                        (person_id, specialty_id, region_id, workplace_id),
                    )

                    summary = (
                        "Initial record created "
                        f"(Region={region_name}, Workplace={workplace_name}, "
                        f"Specialty={specialty_name})"
                    )
                    write_audit_entry(
                        conn=conn,
                        person_id=person_id,
                        batch_id=batch_id,
                        action_type="NEW",
                        summary=summary,
                    )

                elif action_type == "UPDATE":
                    if not person_id:
                        raise ValueError("UPDATE record is missing person_id")

                    old = cur.execute(
                        """
                        SELECT specialty_id, region_id, workplace_id
                        FROM persons
                        WHERE person_id = ?
                        """,
                        (person_id,),
                    ).fetchone()
                    if not old:
                        raise ValueError("person_id not found for UPDATE action")

                    old_specialty_id, old_region_id, old_workplace_id = old
                    old_specialty = get_dimension_name(
                        cur, *DIMENSIONS["specialty"], old_specialty_id
                    )
                    old_region = get_dimension_name(cur, *DIMENSIONS["region"], old_region_id)
                    old_workplace = get_dimension_name(
                        cur, *DIMENSIONS["workplace"], old_workplace_id
                    )

                    cur.execute(
                        """
                        UPDATE persons
                        SET specialty_id = ?, region_id = ?, workplace_id = ?
                        WHERE person_id = ?
                        """,
                        (specialty_id, region_id, workplace_id, person_id),
                    )

                    summary_parts: List[str] = []
                    if old_specialty != specialty_name:
                        summary_parts.append(
                            f"Specialty changed: {old_specialty} -> {specialty_name}"
                        )
                    if old_region != region_name:
                        summary_parts.append(
                            f"Region changed: {old_region} -> {region_name}"
                        )
                    if old_workplace != workplace_name:
                        summary_parts.append(
                            f"Workplace changed: {old_workplace} -> {workplace_name}"
                        )

                    if not summary_parts:
                        summary_parts.append("No data change detected")

                    write_audit_entry(
                        conn=conn,
                        person_id=person_id,
                        batch_id=batch_id,
                        action_type="UPDATE",
                        summary=" | ".join(summary_parts),
                    )

                else:
                    raise ValueError(f"Unsupported action_type: {action_type_raw}")

                cur.execute(
                    """
                    UPDATE workforce_staging
                    SET status = 'APPLIED'
                    WHERE staging_id = ?
                    """,
                    (staging_id,),
                )
                applied_rows += 1

            except Exception as row_error:
                rejected_rows += 1
                error_note = f"APPLY_ERROR: {row_error}"
                cur.execute(
                    """
                    UPDATE workforce_staging
                    SET status = 'REJECTED'
                    WHERE staging_id = ?
                    """,
                    (staging_id,),
                )
                append_source_note(cur, staging_id, error_note)

        if applied_rows == 0:
            batch_status = "REJECTED"
        elif rejected_rows == 0:
            batch_status = "APPLIED"
        else:
            batch_status = "PARTIAL_APPLIED"

        cur.execute(
            """
            UPDATE cbi_batches
            SET status = ?
            WHERE batch_id = ?
            """,
            (batch_status, batch_id),
        )

        conn.commit()
        return {
            "batch_id": batch_id,
            "total_rows": len(rows),
            "applied_rows": applied_rows,
            "rejected_rows": rejected_rows,
            "batch_status": batch_status,
        }

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _create_auto_batch_for_unassigned_approved(conn: sqlite3.Connection) -> Optional[int]:
    cur = conn.cursor()
    count = cur.execute(
        """
        SELECT COUNT(*)
        FROM workforce_staging
        WHERE status = 'APPROVED'
          AND batch_id IS NULL
        """
    ).fetchone()[0]

    if count == 0:
        return None

    batch_name = f"AUTO_APPROVED_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    cur.execute(
        """
        INSERT INTO cbi_batches (batch_name, source_type, status)
        VALUES (?, ?, 'APPROVED')
        """,
        (batch_name, "SYSTEM_AUTO"),
    )
    batch_id = int(cur.lastrowid)
    cur.execute(
        """
        UPDATE workforce_staging
        SET batch_id = ?
        WHERE status = 'APPROVED'
          AND batch_id IS NULL
        """,
        (batch_id,),
    )
    return batch_id


def apply_approved_changes(batch_id: Optional[int] = None) -> List[Dict[str, int]]:
    if batch_id is not None:
        return [apply_batch(batch_id)]

    conn = get_conn()
    try:
        _create_auto_batch_for_unassigned_approved(conn)
        rows = conn.execute(
            """
            SELECT batch_id
            FROM cbi_batches
            WHERE status = 'APPROVED'
            ORDER BY created_at, batch_id
            """
        ).fetchall()
        conn.commit()
    finally:
        conn.close()

    batch_ids = [int(row[0]) for row in rows]
    return [apply_batch(bid) for bid in batch_ids]
