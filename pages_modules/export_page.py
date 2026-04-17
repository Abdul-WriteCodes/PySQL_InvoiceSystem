import streamlit as st
from core.exporter import papers_to_csv, papers_to_excel, synthesis_to_docx


def render():
    papers = st.session_state.get("extracted_papers", [])
    synthesis = st.session_state.get("synthesis_result")

    st.markdown("""
    <div class="page-header">
        <div class="page-eyebrow">Step 04 · Export</div>
        <h1 class="page-title">Export <em>Intelligence</em></h1>
        <p class="page-subtitle">
            Download your extracted data and synthesis report in your preferred format.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not papers:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📥</div>
            <div class="empty-state-title">Nothing to export yet</div>
            <div class="empty-state-desc">Extract papers first to enable exports.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Upload Papers"):
            st.session_state["page"] = "upload"
            st.rerun()
        return

    st.markdown(f"**{len(papers)} paper(s)** ready for export.")
    st.markdown("---")

    # ── Paper Extraction Exports ──────────────────────────────
    st.markdown("### 📊 Paper Extraction Data")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="export-card">
            <span class="export-icon">📋</span>
            <div class="export-name">CSV</div>
            <div class="export-desc">Universal spreadsheet format</div>
        </div>
        """, unsafe_allow_html=True)
        try:
            csv_bytes = papers_to_csv(papers)
            st.download_button(
                "⬇  Download CSV",
                data=csv_bytes,
                file_name="empiricx_results.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_csv",
            )
        except Exception as e:
            st.error(f"CSV error: {e}")

    with col2:
        st.markdown("""
        <div class="export-card">
            <span class="export-icon">📗</span>
            <div class="export-name">Excel</div>
            <div class="export-desc">Formatted .xlsx with styling</div>
        </div>
        """, unsafe_allow_html=True)
        try:
            excel_bytes = papers_to_excel(papers)
            st.download_button(
                "⬇  Download Excel",
                data=excel_bytes,
                file_name="empiricx_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="dl_excel",
            )
        except Exception as e:
            st.error(f"Excel error: {e}")

    # ── Synthesis Export ──────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🔗 Synthesis Report")

    if not synthesis:
        st.info("Run the Cross-Paper Synthesis first to enable the report download.")
        if st.button("→ Go to Synthesis"):
            st.session_state["page"] = "synthesis"
            st.rerun()
        return

    st.markdown("""
    <div class="export-card" style="max-width:380px">
        <span class="export-icon">📄</span>
        <div class="export-name">Word Document (.docx)</div>
        <div class="export-desc">
            Professionally formatted synthesis report with overview, findings, gaps,
            methodology patterns, and a full paper reference table.
        </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        docx_bytes = synthesis_to_docx(synthesis, papers)
        st.download_button(
            "⬇  Download Synthesis Report (.docx)",
            data=docx_bytes,
            file_name="empiricx_synthesis_report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=False,
            key="dl_docx",
        )
    except Exception as e:
        st.error(f"DOCX generation error: {e}")
