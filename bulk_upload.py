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
    page_title="Workforce – Bulk Upload (CBI)",
    layout="centered"
)

st.title("Workforce – Bulk Upload")
st.caption("Phase 6 · Controlled Bulk Intake · Staging Only")


# ================= Helpers =================
def get_conn():
    return sqlite3.connect(DB_PATH)


REQUIRED_COLUMNS = [
    "action_type",
    "specialty_name",
    "region_name",
    "workplace_name",
]


def validate_columns(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return missing


# ================= UI =================
uploaded = st.file_uploader(
    "Upload Excel or CSV file",
    type=["xlsx", "csv"]
)

if not uploaded:
    st.info("Upload a file to begin.")
    st.stop()


# ================= Load File =================
try:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
except Exception as e:
    st.error(f"Failed to read file: {e}")
    st.stop()

st.subheader("Preview")
st.dataframe(df.head(20), use_container_width=True)

# ================= Validation =================
missing_cols = validate_columns(df)

if missing_cols:
    st.error(f"Missing required columns: {missing_cols}")
    st.stop()

if "action_type" in df.columns:
    invalid_actions = df[~df["action_type"].isin(["NEW", "UPDATE"])]
    if not invalid_actions.empty:
        st.error("Invalid action_type values found (allowed: NEW, UPDATE).")
        st.stop()

st.success("File structure validated successfully.")

# ================= Insert to Staging =================
if st.button("Load into Staging (PENDING)", type="primary"):
    conn = get_conn()
    cur = conn.cursor()

    inserted = 0

    for _, row in df.iterrows():
        cur.execute(
            """
            INSERT INTO workforce_staging
            (
                person_id,
                action_type,
                specialty_name,
                region_name,
                workplace_name,
                source_note
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(row.get("person_id")).strip()
                if pd.notna(row.get("person_id")) else None,
                row["action_type"],
                row["specialty_name"],
                row["region_name"],
                row["workplace_name"],
                row.get("source_note"),
            )
        )
        inserted += 1

    conn.commit()
    conn.close()

    st.success(f"{inserted} records loaded into staging (PENDING).")
    st.info("Proceed to Review tab to approve records.")
