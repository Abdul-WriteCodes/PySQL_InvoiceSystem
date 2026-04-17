import streamlit as st
import pandas as pd


DISPLAY_COLS = [
    ("author_year", "Author & Year"),
    ("research_context", "Research Context"),
    ("methodology", "Methodology"),
    ("independent_variables", "IVs"),
    ("dependent_variable", "DV"),
    ("findings", "Key Findings"),
    ("strengths", "Strengths"),
    ("limitations", "Limitations"),
]


def render():
    papers = st.session_state.get("extracted_papers", [])

    st.markdown("""
    <div class="page-header">
        <div class="page-eyebrow">Step 02 · Analyse</div>
        <h1 class="page-title">Extraction <em>Results</em></h1>
        <p class="page-subtitle">
            Structured empirical data extracted from each paper. 
            Inspect the table, drill into individual papers, or proceed to synthesis.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not papers:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <div class="empty-state-title">No papers extracted yet</div>
            <div class="empty-state-desc">Upload and extract papers first to see results here.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Go to Upload"):
            st.session_state["page"] = "upload"
            st.rerun()
        return

    # ── Metrics ──────────────────────────────────────────────────
    methods = [p.get("methodology", "") for p in papers if p.get("methodology")]
    from collections import Counter
    method_counts = Counter(methods)
    top_method = method_counts.most_common(1)[0][0] if method_counts else "—"

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-chip">
            <div class="metric-chip-value">{len(papers)}</div>
            <div class="metric-chip-label">Papers</div>
        </div>
        <div class="metric-chip">
            <div class="metric-chip-value">{len(set(methods))}</div>
            <div class="metric-chip-label">Methodologies</div>
        </div>
        <div class="metric-chip">
            <div class="metric-chip-value" style="font-size:1rem;padding-top:4px">{top_method[:20]}</div>
            <div class="metric-chip-label">Top Method</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── View toggle ───────────────────────────────────────────────
    tab1, tab2 = st.tabs(["📋  Summary Table", "🔍  Paper Detail View"])

    with tab1:
        _render_table(papers)

    with tab2:
        _render_detail(papers)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔗  Run Cross-Paper Synthesis →", type="primary", use_container_width=True):
            st.session_state["page"] = "synthesis"
            st.rerun()
    with col2:
        if st.button("📥  Export Data →", use_container_width=True):
            st.session_state["page"] = "export"
            st.rerun()


def _render_table(papers):
    """Render the main summary table using st.dataframe."""
    rows = []
    for p in papers:
        row = {label: p.get(key, "—") for key, label in DISPLAY_COLS}
        rows.append(row)

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        height=min(600, 80 + 60 * len(papers)),
        column_config={
            "Author & Year": st.column_config.TextColumn(width="small"),
            "Research Context": st.column_config.TextColumn(width="medium"),
            "Methodology": st.column_config.TextColumn(width="small"),
            "IVs": st.column_config.TextColumn(width="medium"),
            "DV": st.column_config.TextColumn(width="small"),
            "Key Findings": st.column_config.TextColumn(width="large"),
            "Strengths": st.column_config.TextColumn(width="medium"),
            "Limitations": st.column_config.TextColumn(width="medium"),
        },
        hide_index=True,
    )


def _render_detail(papers):
    """Per-paper detailed view."""
    if not papers:
        return

    paper_options = [
        f"{i+1}. {p.get('author_year', 'Unknown')} — {p.get('_source_file', '')}"
        for i, p in enumerate(papers)
    ]

    selected_idx = st.selectbox("Select a paper", range(len(paper_options)),
                                 format_func=lambda i: paper_options[i],
                                 label_visibility="collapsed")

    p = papers[selected_idx]

    # Title
    st.markdown(f"""
    <div class="x-card x-card-accent">
        <div class="page-eyebrow">{p.get('author_year', '')}</div>
        <div style="font-family: var(--font-display); font-size: 1.3rem; color: var(--text-primary); margin-bottom: 8px;">
            {p.get('title', 'Untitled')}
        </div>
        <div style="font-size:0.85rem; color:var(--text-muted);">{p.get('_source_file', '')}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        _detail_block("📍 Research Context", p.get("research_context", "—"))
        _detail_block("⚙️ Methodology", p.get("methodology", "—"))
        _detail_block("📌 Independent Variables", p.get("independent_variables", "—"))
        _detail_block("🎯 Dependent Variable", p.get("dependent_variable", "—"))
        _detail_block("🔧 Control Variables", p.get("control_variables", "—"))

    with col2:
        _detail_block("📊 Key Findings", p.get("findings", "—"))
        _detail_block("💡 Theoretical Contributions", p.get("theoretical_contributions", "—"))
        _detail_block("🏭 Practical Contributions", p.get("practical_contributions", "—"))
        _detail_block("✅ Strengths", p.get("strengths", "—"))
        _detail_block("⚠️ Limitations", p.get("limitations", "—"))

    # Citations
    with st.expander("📚 View Citations"):
        st.markdown("**APA 7th Edition**")
        st.code(p.get("citation_apa", "Not available"), language=None)
        st.markdown("**MLA 9th Edition**")
        st.code(p.get("citation_mla", "Not available"), language=None)
        st.markdown("**Harvard**")
        st.code(p.get("citation_harvard", "Not available"), language=None)


def _detail_block(label: str, content: str):
    st.markdown(f"""
    <div class="x-card" style="padding: 1rem 1.2rem; margin-bottom: 0.75rem;">
        <div style="font-family: var(--font-mono); font-size: 0.65rem; letter-spacing: 1.5px;
                    text-transform: uppercase; color: var(--text-muted); margin-bottom: 6px;">
            {label}
        </div>
        <div style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6;">
            {content}
        </div>
    </div>
    """, unsafe_allow_html=True)
