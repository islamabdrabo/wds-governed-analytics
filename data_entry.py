import sqlite3

import pandas as pd
import streamlit as st

from config.paths import DB_PATH

REQUIRED_COLUMNS = [
    "action_type",
    "specialty_name",
    "region_name",
    "workplace_name",
]


def get_conn():
    return sqlite3.connect(DB_PATH)


def run_data_entry():
    st.subheader("Controlled Data Entry")
    st.caption("Controlled Intake · File Upload to Staging Only")

    uploaded = st.file_uploader(
        "Upload Excel or CSV file",
        type=["xlsx", "csv"],
    )

    if not uploaded:
        st.info("Upload a file to add records into staging (no apply).")
        return

    try:
        if uploaded.name.lower().endswith(".csv"):
            df = pd.read_csv(uploaded)
        else:
            df = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Failed to read file: {e}")
        return

    st.subheader("Preview")
    st.dataframe(df.head(20), use_container_width=True)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"Missing required columns: {missing}")
        return

    df["action_type"] = df["action_type"].astype(str).str.strip().str.upper()
    invalid = df[~df["action_type"].isin(["NEW", "UPDATE"])]
    if not invalid.empty:
        st.error("Invalid action_type values found (allowed: NEW, UPDATE).")
        return

    if "person_id" in df.columns:
        update_mask = df["action_type"] == "UPDATE"
        update_person_ids = (
            df.loc[update_mask, "person_id"]
            .astype(str)
            .str.strip()
            .str.lower()
        )
        if update_person_ids.isin(["", "nan", "none"]).any():
            st.error("UPDATE records must include person_id.")
            return
    elif (df["action_type"] == "UPDATE").any():
        st.error("Column person_id is required for UPDATE records.")
        return

    st.success("File validated successfully.")

    if st.button("Load into Staging (PENDING)", type="primary"):
        conn = get_conn()
        cur = conn.cursor()

        try:
            cur.execute(
                """
                INSERT INTO cbi_batches (batch_name, source_type, status)
                VALUES (?, ?, 'PENDING')
                """,
                (uploaded.name, "FILE_UPLOAD"),
            )
            batch_id = cur.lastrowid

            inserted = 0
            for _, row in df.iterrows():
                person_value = row.get("person_id")
                person_id = (
                    str(person_value).strip()
                    if pd.notna(person_value) and str(person_value).strip()
                    else None
                )

                cur.execute(
                    """
                    INSERT INTO workforce_staging
                    (
                        person_id,
                        action_type,
                        specialty_name,
                        region_name,
                        workplace_name,
                        source_note,
                        batch_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        person_id,
                        row["action_type"],
                        str(row["specialty_name"]).strip(),
                        str(row["region_name"]).strip(),
                        str(row["workplace_name"]).strip(),
                        row.get("source_note"),
                        batch_id,
                    ),
                )
                inserted += 1

            conn.commit()
        except Exception as e:
            conn.rollback()
            st.error(f"Failed to insert into staging: {e}")
            conn.close()
            return

        conn.close()

        st.success(f"{inserted} records loaded into staging batch #{batch_id} (PENDING).")
        st.info("Proceed to Batch Review to approve or reject this batch.")
