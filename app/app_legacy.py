import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import io
import importlib.util
import sys

# ================= Page Config =================
st.set_page_config(
    page_title="Workforce Analytics – Phase 1",
    layout="wide"
)

# ================= Paths =================
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "db" / "workforce.db"
EXPORT_SCRIPT_PATH = BASE_DIR / "import" / "06_export_excel.py"

# ================= Load export_official_excel dynamically =================
spec = importlib.util.spec_from_file_location(
    "export_module", EXPORT_SCRIPT_PATH
)
export_module = importlib.util.module_from_spec(spec)
sys.modules["export_module"] = export_module
spec.loader.exec_module(export_module)

export_official_excel = export_module.export_official_excel

# ================= Data Load =================
@st.cache_data
def load_base():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM v_workforce_base_canonical", conn)
    conn.close()
    return df

df = load_base()

# ================= Title =================
st.title("Workforce Analytics")
st.caption("Canonical View · Read-only · Phase 1")

# ================= Sidebar Filters =================
with st.sidebar:
    st.header("Filters")

    # ---------- Region ----------
    st.subheader("Region")
    all_regions = sorted(df["region_name"].dropna().unique().tolist())
    if "region_selection" not in st.session_state:
        st.session_state.region_selection = all_regions.copy()

    c1, c2 = st.columns(2)
    if c1.button("Select All", key="region_all"):
        st.session_state.region_selection = all_regions.copy()
    if c2.button("Clear All", key="region_clear"):
        st.session_state.region_selection = []

    st.session_state.region_selection = st.multiselect(
        "Choose Regions",
        all_regions,
        default=st.session_state.region_selection
    )

    st.divider()

    # ---------- Specialty ----------
    st.subheader("Specialty")
    all_specialties = sorted(df["specialty_name"].dropna().unique().tolist())
    if "specialty_selection" not in st.session_state:
        st.session_state.specialty_selection = all_specialties.copy()

    c1, c2 = st.columns(2)
    if c1.button("Select All", key="spec_all"):
        st.session_state.specialty_selection = all_specialties.copy()
    if c2.button("Clear All", key="spec_clear"):
        st.session_state.specialty_selection = []

    st.session_state.specialty_selection = st.multiselect(
        "Choose Specialties",
        all_specialties,
        default=st.session_state.specialty_selection
    )

    st.divider()

    # ---------- Workplace ----------
    st.subheader("Workplace")
    all_workplaces = sorted(df["workplace_name"].dropna().unique().tolist())
    if "workplace_selection" not in st.session_state:
        st.session_state.workplace_selection = all_workplaces.copy()

    c1, c2 = st.columns(2)
    if c1.button("Select All", key="wp_all"):
        st.session_state.workplace_selection = all_workplaces.copy()
    if c2.button("Clear All", key="wp_clear"):
        st.session_state.workplace_selection = []

    st.session_state.workplace_selection = st.multiselect(
        "Choose Workplaces",
        all_workplaces,
        default=st.session_state.workplace_selection
    )

# ================= Apply Filters =================
filtered_df = df.copy()

if st.session_state.region_selection:
    filtered_df = filtered_df[
        filtered_df["region_name"].isin(st.session_state.region_selection)
    ]

if st.session_state.specialty_selection:
    filtered_df = filtered_df[
        filtered_df["specialty_name"].isin(st.session_state.specialty_selection)
    ]

if st.session_state.workplace_selection:
    filtered_df = filtered_df[
        filtered_df["workplace_name"].isin(st.session_state.workplace_selection)
    ]

# ================= KPIs =================
c1, c2, c3 = st.columns(3)
c1.metric("Persons", filtered_df["person_id"].nunique())
c2.metric("Specialties", filtered_df["specialty_name"].nunique())
c3.metric("Workplaces", filtered_df["workplace_name"].nunique())

st.divider()

# ================= Table =================
st.subheader("Filtered Workforce Records")
st.dataframe(
    filtered_df,
    use_container_width=True,
    height=500
)

# ================= Export =================
st.divider()
st.subheader("Export")

output = io.BytesIO()
export_official_excel(filtered_df, output)

st.download_button(
    label="Download Official Report (Exact Baseline)",
    data=output.getvalue(),
    file_name="Workforce_Report_Filtered.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
