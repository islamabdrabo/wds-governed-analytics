import sqlite3

import streamlit as st

from config.paths import DB_PATH


def run_audit_timeline():
    st.subheader("Audit Timeline")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    table_names = [t["name"] for t in tables]

    if "workforce_audit_timeline" not in table_names:
        st.warning("Audit timeline table is not yet available.")
        st.info("Audit tracking will appear here once enabled.")
        conn.close()
        return

    df = conn.execute(
        """
        SELECT person_id, batch_id, action_type, change_summary, applied_at
        FROM workforce_audit_timeline
        ORDER BY applied_at DESC
        LIMIT 200
        """
    ).fetchall()

    st.dataframe(df, use_container_width=True)
    conn.close()
