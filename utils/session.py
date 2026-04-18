import streamlit as st

def init_session():
    defaults = {
        "authenticated": False,
        "page": "results",
        "queued_files": [],
        "extracted_papers": [],
        "synthesis_result": None,
        "processing_errors": [],
        "trigger_extract": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
