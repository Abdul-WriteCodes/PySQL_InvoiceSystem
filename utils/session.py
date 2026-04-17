import streamlit as st

def init_session():
    defaults = {
        "page": "upload",
        "openai_api_key": "",
        "uploaded_files_info": [],      # List of {name, size, content_bytes}
        "extracted_papers": [],         # List of PaperResult dicts
        "synthesis_result": None,       # Synthesis output dict
        "processing_errors": [],        # List of error strings
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
