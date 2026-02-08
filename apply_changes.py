import sqlite3

import streamlit as st

from cbi.apply_engine import apply_approved_changes
from config.paths import DB_PATH


def get_conn():
    return sqlite3.connect(DB_PATH)


def count_approved():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM workforce_staging WHERE status = 'APPROVED'"
    )
    count = cur.fetchone()[0]
    conn.close()
    return count


def run_apply_changes():
    st.subheader("Apply Approved Changes")
    st.caption("Controlled Apply · Approved Records Only")

    approved_count = count_approved()
    st.metric("Approved records ready to apply", approved_count)

    st.divider()

    if approved_count == 0:
        st.info("No approved records to apply.")
        return

    st.warning(
        "This action will permanently apply all APPROVED records to the core workforce data."
    )

    if st.button("Apply Approved Changes", type="primary"):
        try:
            with st.spinner("Applying approved changes..."):
                results = apply_approved_changes()
        except Exception as e:
            st.error(f"Apply failed: {e}")
            return

        if not results:
            st.warning("No approved batches found.")
            return

        total_applied = sum(r["applied_rows"] for r in results)
        total_rejected = sum(r["rejected_rows"] for r in results)

        st.success(
            f"Apply completed. Applied={total_applied}, Rejected={total_rejected}."
        )

        st.subheader("Batch Results")
        for result in results:
            st.write(
                f"Batch #{result['batch_id']}: "
                f"status={result['batch_status']}, "
                f"applied={result['applied_rows']}, "
                f"rejected={result['rejected_rows']}."
            )
