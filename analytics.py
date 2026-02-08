import importlib.util
import sqlite3
import sys
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from config.paths import DB_PATH, PROJECT_ROOT

EXPORT_SCRIPT = PROJECT_ROOT / "import" / "06_export_excel.py"
CANONICAL_VIEW = "v_workforce_base_canonical"

spec = importlib.util.spec_from_file_location("export_module", EXPORT_SCRIPT)
export_module = importlib.util.module_from_spec(spec)
sys.modules["export_module"] = export_module
assert spec.loader is not None
spec.loader.exec_module(export_module)
export_official_excel = export_module.export_official_excel


def reconcile_state(current, options):
    return [v for v in current if v in options]


def run_analytics():
    st.subheader("Analytics")

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(f"SELECT * FROM {CANONICAL_VIEW}", conn)
    conn.close()

    st.sidebar.header("Filters")

    regions = sorted(df["region_name"].dropna().unique().tolist())
    st.session_state.setdefault("region_sel", [])

    c1, c2 = st.sidebar.columns(2)
    if c1.button("Select All", key="r_all"):
        st.session_state.region_sel = regions.copy()
    if c2.button("Clear All", key="r_clear"):
        st.session_state.region_sel = []

    st.session_state.region_sel = st.sidebar.multiselect(
        "Region", regions, default=st.session_state.region_sel
    )

    if not st.session_state.region_sel:
        st.info("Select at least one Region to load data.")
        return

    wp_df = df[df["region_name"].isin(st.session_state.region_sel)]
    workplaces = sorted(wp_df["workplace_name"].dropna().unique().tolist())

    st.session_state.setdefault("wp_sel", [])
    st.session_state.wp_sel = reconcile_state(st.session_state.wp_sel, workplaces)

    c1, c2 = st.sidebar.columns(2)
    if c1.button("Select All", key="w_all"):
        st.session_state.wp_sel = workplaces.copy()
    if c2.button("Clear All", key="w_clear"):
        st.session_state.wp_sel = []

    st.session_state.wp_sel = st.sidebar.multiselect(
        "Workplace", workplaces, default=st.session_state.wp_sel
    )

    sp_df = (
        wp_df[wp_df["workplace_name"].isin(st.session_state.wp_sel)]
        if st.session_state.wp_sel
        else wp_df
    )
    specialties = sorted(sp_df["specialty_name"].dropna().unique().tolist())

    st.session_state.setdefault("sp_sel", [])
    st.session_state.sp_sel = reconcile_state(st.session_state.sp_sel, specialties)

    c1, c2 = st.sidebar.columns(2)
    if c1.button("Select All", key="s_all"):
        st.session_state.sp_sel = specialties.copy()
    if c2.button("Clear All", key="s_clear"):
        st.session_state.sp_sel = []

    st.session_state.sp_sel = st.sidebar.multiselect(
        "Specialty", specialties, default=st.session_state.sp_sel
    )

    fdf = df.copy()
    if st.session_state.region_sel:
        fdf = fdf[fdf["region_name"].isin(st.session_state.region_sel)]
    if st.session_state.wp_sel:
        fdf = fdf[fdf["workplace_name"].isin(st.session_state.wp_sel)]
    if st.session_state.sp_sel:
        fdf = fdf[fdf["specialty_name"].isin(st.session_state.sp_sel)]

    if fdf.empty:
        st.info("No data for selected filters.")
        return

    st.dataframe(fdf, use_container_width=True)

    buffer = BytesIO()
    export_official_excel(fdf, buffer)

    st.download_button(
        "Download Official Report",
        data=buffer.getvalue(),
        file_name="Workforce_Analytics_Official.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
