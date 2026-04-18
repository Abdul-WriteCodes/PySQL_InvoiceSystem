import streamlit as st
from core.exporter import papers_to_csv, papers_to_excel, synthesis_to_docx

def render():
    papers    = st.session_state.get("extracted_papers", [])
    synthesis = st.session_state.get("synthesis_result")

    st.markdown("""
    <div class="ph-wrap anim-up">
      <div class="ph-eye">Step 03 · Export</div>
      <h1 class="ph-title">Export <em>Intelligence</em></h1>
      <p class="ph-sub">Download your structured extraction data and synthesis report.</p>
    </div>""", unsafe_allow_html=True)

    if not papers:
        st.markdown("""
        <div class="empty-st">
          <div class="empty-st-icon">📥</div>
          <div class="empty-st-title">Nothing to export yet</div>
          <div class="empty-st-desc">Extract papers first to enable downloads.</div>
        </div>""", unsafe_allow_html=True)
        return

    # Section header
    st.markdown(f"""
    <div style="font-family:var(--f-mono);font-size:var(--tx-2xs);letter-spacing:0.14em;
                text-transform:uppercase;color:var(--teal);margin-bottom:var(--gap-sm);
                display:flex;align-items:center;gap:8px;opacity:0.85">
      Paper Extraction Data &nbsp;·&nbsp; {len(papers)} paper(s)
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="exp-card">
          <span class="exp-icon">📋</span>
          <div class="exp-name">CSV Spreadsheet</div>
          <div class="exp-desc">Universal format — opens in Excel, Sheets, or any analysis tool</div>
        </div>""", unsafe_allow_html=True)
        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
        try:
            st.download_button("⬇  Download CSV", data=papers_to_csv(papers),
                file_name="empiricx_results.csv", mime="text/csv",
                use_container_width=True, key="dl_csv")
        except Exception as e:
            st.error(f"Error: {e}")

    with c2:
        st.markdown("""
        <div class="exp-card">
          <span class="exp-icon">📗</span>
          <div class="exp-name">Excel Workbook</div>
          <div class="exp-desc">Styled .xlsx with freeze panes, alternating rows, column widths</div>
        </div>""", unsafe_allow_html=True)
        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
        try:
            st.download_button("⬇  Download Excel", data=papers_to_excel(papers),
                file_name="empiricx_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True, key="dl_excel")
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("""
    <div style="font-family:var(--f-mono);font-size:var(--tx-2xs);letter-spacing:0.14em;
                text-transform:uppercase;color:var(--teal);margin-bottom:var(--gap-sm);
                opacity:0.85">
      Synthesis Report
    </div>""", unsafe_allow_html=True)

    if not synthesis:
        st.markdown("""
        <div class="x-card" style="text-align:center;padding:clamp(1.75rem,5vw,2.5rem)">
          <div style="font-size:2.2rem;margin-bottom:14px;opacity:0.25">📄</div>
          <div style="font-size:var(--tx-sm);color:var(--ink-2);margin-bottom:18px;font-weight:500">
            Run Cross-Paper Synthesis first to generate the Word report.
          </div>
        </div>""", unsafe_allow_html=True)
        if st.button("→  Go to Synthesis"):
            st.session_state["page"] = "synthesis"; st.rerun()
        return

    st.markdown("""
    <div class="exp-card" style="text-align:left;max-width:520px">
      <div style="display:flex;align-items:flex-start;gap:18px">
        <span style="font-size:2.4rem;flex-shrink:0">📄</span>
        <div>
          <div class="exp-name">Word Document (.docx)</div>
          <div class="exp-desc" style="margin-top:8px;line-height:1.6">
            Complete synthesis report — executive overview, all six insight sections,
            underexplored variables, dominant methodology, and a full paper reference table.
            Ready to paste into your literature review.
          </div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

    try:
        st.download_button("⬇  Download Synthesis Report (.docx)",
            data=synthesis_to_docx(synthesis, papers),
            file_name="empiricx_synthesis_report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="dl_docx")
    except Exception as e:
        st.error(f"DOCX error: {e}")
