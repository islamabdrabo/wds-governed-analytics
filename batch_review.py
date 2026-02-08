import sqlite3

import pandas as pd
import streamlit as st

from config.paths import DB_PATH


def run_batch_review():
    st.subheader("Batch Review")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    df_batches = pd.read_sql(
        """
        SELECT
            batch_id,
            batch_name,
            status,
            created_at
        FROM cbi_batches
        ORDER BY created_at DESC
        """,
        conn,
    )

    if df_batches.empty:
        st.info("No batches available for review.")
        conn.close()
        return

    selected_batch_id = st.selectbox(
        "Select batch_id",
        options=df_batches["batch_id"].tolist(),
    )

    batch_row = df_batches[df_batches["batch_id"] == selected_batch_id]
    if batch_row.empty:
        st.warning("Selected batch not found.")
        conn.close()
        return

    batch_row = batch_row.iloc[0]
    st.markdown(
        f"""
    **Batch Name:** {batch_row["batch_name"]}  
    **Status:** `{batch_row["status"]}`  
    **Created At:** {batch_row["created_at"]}
    """
    )

    df_records = pd.read_sql(
        """
        SELECT
            staging_id,
            person_id,
            action_type,
            specialty_name,
            region_name,
            workplace_name,
            status
        FROM workforce_staging
        WHERE batch_id = ?
        ORDER BY staging_id
        """,
        conn,
        params=[selected_batch_id],
    )

    if df_records.empty:
        st.info("No records found for this batch.")
        conn.close()
        return

    st.subheader("Staging Records")
    st.dataframe(df_records, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve Batch"):
            conn.execute(
                "UPDATE cbi_batches SET status = 'APPROVED' WHERE batch_id = ?",
                (selected_batch_id,),
            )
            conn.execute(
                "UPDATE workforce_staging SET status = 'APPROVED' WHERE batch_id = ?",
                (selected_batch_id,),
            )
            conn.commit()
            st.success("Batch approved successfully.")

    with col2:
        if st.button("Reject Batch"):
            conn.execute(
                "UPDATE cbi_batches SET status = 'REJECTED' WHERE batch_id = ?",
                (selected_batch_id,),
            )
            conn.execute(
                "UPDATE workforce_staging SET status = 'REJECTED' WHERE batch_id = ?",
                (selected_batch_id,),
            )
            conn.commit()
            st.error("Batch rejected.")

    conn.close()
