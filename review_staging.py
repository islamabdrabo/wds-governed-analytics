import sys
from pathlib import Path

# --- Ensure project root is on sys.path ---
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import sqlite3
import pandas as pd

from config.paths import DB_PATH

# ================= Page Config =================
st.set_page_config(
    page_title="Workforce – Review & Approve",
    layout="wide"
)

# ================= DB Helpers =================
def get_conn():
    return sqlite3.connect(DB_PATH)

def load_staging():
    conn = get_conn()
    df = pd.read_sql(
        """
        SELECT
            staging_id,
            action_type,
            person_id,
            specialty_name,
            region_name,
            workplace_name,
            status,
            source_note,
            created_at
        FROM workforce_staging
        ORDER BY created_at DESC
        """,
        conn
    )
    conn.close()
    return df

def update_status(staging_id, new_status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE workforce_staging SET status = ? WHERE staging_id = ?",
        (new_status, staging_id)
    )
    conn.commit()
    conn.close()

# ================= UI =================
st.title("Workforce – Review & Approve")
st.caption("Phase 2 · Staging Review · No Apply Yet")

df = load_staging()

if df.empty:
    st.info("No staging records found.")
    st.stop()

# -------- Filters --------
with st.sidebar:
    st.header("Filter")
    status_filter = st.multiselect(
        "Status",
        options=["PENDING", "APPROVED", "REJECTED"],
        default=["PENDING"]
    )

if status_filter:
    df = df[df["status"].isin(status_filter)]

# -------- Table --------
st.subheader("Staging Records")
st.dataframe(
    df,
    use_container_width=True,
    height=400
)

st.divider()

# -------- Actions --------
st.subheader("Review Action")

selected_id = st.selectbox(
    "Select staging_id",
    options=df["staging_id"].tolist()
)

col1, col2 = st.columns(2)

with col1:
    if st.button("Approve"):
        update_status(selected_id, "APPROVED")
        st.success(f"Record {selected_id} approved")
        st.rerun()

with col2:
    if st.button("Reject"):
        update_status(selected_id, "REJECTED")
        st.warning(f"Record {selected_id} rejected")
        st.rerun()
