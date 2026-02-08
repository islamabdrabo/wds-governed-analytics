import sys
from pathlib import Path

import streamlit as st

# Ensure project root is on PYTHONPATH.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.set_page_config(
    page_title="Workforce Data System",
    layout="wide",
)

st.title("Workforce Data System")
st.caption("Governed Workforce Platform · Analytics · Batch Governance")

st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Select Module",
    [
        "Analytics",
        "Controlled Data Entry",
        "Batch Review",
        "Apply Changes",
        "Audit Timeline",
    ],
)

if page == "Analytics":
    from phase2.app.analytics import run_analytics

    run_analytics()
elif page == "Controlled Data Entry":
    from phase2.app.data_entry import run_data_entry

    run_data_entry()
elif page == "Batch Review":
    from phase2.app.batch_review import run_batch_review

    run_batch_review()
elif page == "Apply Changes":
    from phase2.app.apply_changes import run_apply_changes

    run_apply_changes()
elif page == "Audit Timeline":
    from phase2.app.audit_timeline import run_audit_timeline

    run_audit_timeline()
