import streamlit as st
from core.extractor import synthesize_papers


SECTION_CONFIG = [
    ("common_findings",      "📈 Common Findings",           "info"),
    ("conflicting_results",  "⚡ Conflicting Results",        "warning"),
    ("methodology_patterns", "⚙️ Methodology Patterns",       "info"),
    ("research_gaps",        "🔭 Research Gaps Identified",   "warning"),
    ("common_weaknesses",    "⚠️ Common Weaknesses",          "warning"),
    ("future_directions",    "🚀 Future Research Directions", "success"),
]


def render():
    papers = st.session_state.get("extracted_papers", [])
    synthesis = st.session_state.get("synthesis_result")

    st.markdown("""
    <div class="page-header">
        <div class="page-eyebrow">Step 03 · Synthesize</div>
        <h1 class="page-title">Cross-Paper <em>Intelligence</em></h1>
        <p class="page-subtitle">
            EmpiricX synthesizes patterns, conflicts, and gaps across your entire paper set —
            the insight layer that transforms a literature review from tedious to strategic.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not papers:
        st.info("Upload and extract at least 2 papers to run synthesis.")
        if st.button("← Upload Papers"):
            st.session_state["page"] = "upload"
            st.rerun()
        return

    if len(papers) < 2:
        st.warning("Upload at least 2 papers for meaningful cross-paper synthesis.")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{len(papers)} papers** loaded and ready for synthesis.")
    with col2:
        run_label = "🔗  Run Synthesis" if not synthesis else "🔄  Re-run"
        run_btn = st.button(run_label, type="primary", use_container_width=True)

    if run_btn:
        with st.spinner("🧠 Synthesizing across papers… this may take 15–30 seconds"):
            try:
                result = synthesize_papers(papers)
                st.session_state["synthesis_result"] = result
                synthesis = result
                st.success("Synthesis complete!")
            except Exception as e:
                st.error(f"Synthesis failed: {e}")
                return

    if not synthesis:
        st.markdown("---")
        st.markdown(
            "Click **Run Synthesis** above to generate cross-paper intelligence."
        )
        return

    _render_synthesis(synthesis)


def _render_synthesis(s: dict):
    st.markdown("---")

    # ── Overall Summary ────────────────────────────────────────
    summary = s.get("overall_summary", "")
    if summary:
        st.subheader("Overview")
        st.info(summary)
        st.markdown("")

    # ── Main two-column sections ───────────────────────────────
    col1, col2 = st.columns(2)

    left_keys  = ["common_findings", "methodology_patterns", "common_weaknesses"]
    right_keys = ["conflicting_results", "research_gaps", "future_directions"]

    section_map = {cfg[0]: cfg for cfg in SECTION_CONFIG}

    with col1:
        for key in left_keys:
            items = s.get(key, [])
            if not items:
                continue
            _, title, kind = section_map[key]
            st.markdown(f"**{title}**")
            for item in items:
                st.markdown(f"- {item}")
            st.markdown("")

    with col2:
        for key in right_keys:
            items = s.get(key, [])
            if not items:
                continue
            _, title, kind = section_map[key]
            st.markdown(f"**{title}**")
            for item in items:
                st.markdown(f"- {item}")
            st.markdown("")

    # ── Underexplored Variables ────────────────────────────────
    unexplored = s.get("underexplored_variables", [])
    if unexplored:
        st.markdown("**🔮 Underexplored Variables**")
        st.markdown("  ".join([f"`{v}`" for v in unexplored]))
        st.markdown("")

    # ── Dominant Methodology ───────────────────────────────────
    dom = s.get("dominant_methodology", "")
    if dom:
        st.markdown("**⚙️ Dominant Methodology**")
        st.success(dom)

    st.markdown("---")

    if st.button("📥  Export Synthesis Report (.docx) →", type="primary"):
        st.session_state["page"] = "export"
        st.rerun()
