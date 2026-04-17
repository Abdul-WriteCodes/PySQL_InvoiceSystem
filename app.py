import streamlit as st
import os
from pathlib import Path

# Page config must be first
st.set_page_config(
    page_title="EmpiricX — Research Intelligence Engine",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Import pages
from pages_modules import upload_page, results_page, synthesis_page, export_page
from utils.session import init_session

# Initialize session state
init_session()

# ─── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <span class="brand-icon">⬡</span>
        <span class="brand-name">EmpiricX</span>
    </div>
    <div class="sidebar-tagline">Research Intelligence Engine</div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # API Key input
    st.markdown('<p class="sidebar-label">OpenAI API Key</p>', unsafe_allow_html=True)
    api_key = st.text_input(
        "API Key",
        value=st.session_state.get("openai_api_key", ""),
        type="password",
        placeholder="sk-...",
        label_visibility="collapsed"
    )
    if api_key:
        st.session_state["openai_api_key"] = api_key
        os.environ["OPENAI_API_KEY"] = api_key

    st.markdown("---")

    # Navigation
    st.markdown('<p class="sidebar-label">Navigation</p>', unsafe_allow_html=True)
    
    nav_options = {
        "📤  Upload Papers": "upload",
        "📊  Extraction Results": "results",
        "🔗  Cross-Paper Synthesis": "synthesis",
        "📥  Export": "export",
    }

    selected_nav = st.radio(
        "nav",
        list(nav_options.keys()),
        index=list(nav_options.values()).index(st.session_state.get("page", "upload")),
        label_visibility="collapsed"
    )
    st.session_state["page"] = nav_options[selected_nav]

    st.markdown("---")

    # Stats
    n_papers = len(st.session_state.get("extracted_papers", []))
    st.markdown(f"""
    <div class="sidebar-stats">
        <div class="stat-item">
            <span class="stat-number">{n_papers}</span>
            <span class="stat-label">Papers Loaded</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sidebar-footer">
        <a href="https://github.com" target="_blank">Docs</a> · 
        <a href="mailto:hello@empiricx.ai">Support</a>
    </div>
    """, unsafe_allow_html=True)

# ─── Main Content ──────────────────────────────────────────────────────────
page = st.session_state.get("page", "upload")

if page == "upload":
    upload_page.render()
elif page == "results":
    results_page.render()
elif page == "synthesis":
    synthesis_page.render()
elif page == "export":
    export_page.render()
