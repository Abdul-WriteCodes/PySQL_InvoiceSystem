import streamlit as st
import os
from pathlib import Path

st.set_page_config(
    page_title="EmpiricX — Research Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────
css_path = Path(__file__).parent / "assets" / "style.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from utils.session import init_session
init_session()

# ── API key from secrets ──────────────────────────────────────────
try:
    key = st.secrets.get("OPENAI_API_KEY", "")
    if key:
        os.environ["OPENAI_API_KEY"] = key
except Exception:
    pass

# ── Password gate ─────────────────────────────────────────────────
def _gate() -> bool:
    try:
        correct = st.secrets.get("APP_PASSWORD", "empiricx2024")
    except Exception:
        correct = "empiricx2024"

    if st.session_state.get("authenticated"):
        return True

    st.markdown('<div class="gate-bg"></div>', unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.5, 1])
    with col:
        st.markdown("""
        <div class="gate-card">
          <div class="gate-logo-wrap">
            <div class="gate-mark"><span class="gate-mark-x">✕</span></div>
            <div class="gate-wordmark">Empiri<span>X</span></div>
            <div class="gate-sub">Research Intelligence Engine</div>
          </div>
          <div class="gate-pill">
            <span class="gate-pill-dot"></span>
            AI-Powered Empirical Analysis
          </div>
          <div class="gate-features">
            <div class="gate-feat"><span class="gate-feat-icon">→</span>Extract 13 structured fields per paper automatically</div>
            <div class="gate-feat"><span class="gate-feat-icon">→</span>Cross-paper synthesis — gaps, conflicts &amp; patterns</div>
            <div class="gate-feat"><span class="gate-feat-icon">→</span>Export to CSV, Excel &amp; Word synthesis report</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        err = st.empty()
        pwd = st.text_input("Access Password", type="password",
                            placeholder="Enter your access password", key="pwd_input")
        go  = st.button("Enter Platform →", use_container_width=True)

        if go or pwd:
            if pwd == correct:
                st.session_state["authenticated"] = True
                st.rerun()
            elif pwd:
                err.markdown(
                    '<div class="gate-error">⚠ Incorrect password — please try again.</div>',
                    unsafe_allow_html=True)

        st.markdown(
            '<div class="gate-footer">Restricted access · <strong>EmpiricX</strong> v1.0</div>',
            unsafe_allow_html=True)

    return False


if not _gate():
    st.stop()

# ═══════════════════════════════════════════════════════
#  AUTHENTICATED APP
# ═══════════════════════════════════════════════════════
from pages_modules import upload_page, results_page, synthesis_page, export_page
from utils.parser import format_file_size

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    # Brand
    st.markdown("""
    <div class="sb-brand">
      <div class="sb-mark"><div class="sb-mark-inner"></div></div>
      <span class="sb-name">EmpiricX</span>
    </div>
    <div class="sb-tagline">Research Intelligence</div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

    # Upload
    st.markdown('<span class="sb-label">📂  Upload Papers</span>', unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "Drop files here",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        help="PDF, DOCX, or TXT · up to 50 MB each",
        key="sidebar_uploader",
    )

    if uploaded:
        queued = st.session_state.get("queued_files", [])
        existing = {f["name"] for f in queued}
        for f in uploaded:
            if f.name not in existing:
                queued.append({"name": f.name, "size": f.size, "obj": f})
                existing.add(f.name)
        st.session_state["queued_files"] = queued

    queued    = st.session_state.get("queued_files", [])
    extracted = st.session_state.get("extracted_papers", [])
    done_names = {p.get("_source_file") for p in extracted}

    if queued:
        st.markdown('<div style="margin-top:10px"></div>', unsafe_allow_html=True)
        for fi in queued:
            done = fi["name"] in done_names
            badge_cls = "sb-badge-ok" if done else "sb-badge-new"
            badge_txt = "Done" if done else "Queued"
            st.markdown(f"""
            <div class="sb-paper">
              <span class="sb-paper-icon">📄</span>
              <div style="min-width:0;flex:1">
                <div class="sb-paper-name">{fi["name"]}</div>
                <div class="sb-paper-meta">{format_file_size(fi["size"])}</div>
              </div>
              <span class="sb-badge {badge_cls}">{badge_txt}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div style="margin-top:10px"></div>', unsafe_allow_html=True)
        pending = [f for f in queued if f["name"] not in done_names]
        if pending:
            if st.button(f"⚡  Extract {len(pending)} paper(s)", use_container_width=True):
                st.session_state["trigger_extract"] = True
                st.session_state["page"] = "results"
                st.rerun()
        if st.button("🗑  Clear all", use_container_width=True):
            for k in ["queued_files","extracted_papers","synthesis_result"]:
                st.session_state[k] = [] if k != "synthesis_result" else None
            st.rerun()

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

    # Nav
    st.markdown('<span class="sb-label">Navigate</span>', unsafe_allow_html=True)
    nav_map = {"📊  Results": "results", "🔗  Synthesis": "synthesis", "📥  Export": "export"}
    cur = st.session_state.get("page","results")
    sel = st.radio("nav", list(nav_map.keys()),
                   index=list(nav_map.values()).index(cur if cur in nav_map.values() else "results"),
                   label_visibility="collapsed", key="main_nav")
    st.session_state["page"] = nav_map[sel]

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

    # Stats
    n  = len(extracted)
    sy = "✓" if st.session_state.get("synthesis_result") else "—"
    st.markdown(f"""
    <div class="sb-stats">
      <div class="sb-stat"><div class="sb-stat-n">{n}</div><div class="sb-stat-l">Papers</div></div>
      <div class="sb-stat"><div class="sb-stat-n">{sy}</div><div class="sb-stat-l">Synthesis</div></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)
    if st.button("⎋  Sign out", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# ── MAIN ──────────────────────────────────────────────────────────
if st.session_state.pop("trigger_extract", False):
    upload_page.run_extraction_from_queue()

page = st.session_state.get("page","results")
if   page == "results":   results_page.render()
elif page == "synthesis": synthesis_page.render()
elif page == "export":    export_page.render()
