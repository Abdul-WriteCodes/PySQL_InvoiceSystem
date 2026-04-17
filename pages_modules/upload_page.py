import streamlit as st
from utils.parser import extract_text, format_file_size, smart_truncate
from core.extractor import extract_paper
import traceback


def render():
    st.markdown("""
    <div class="page-header">
        <div class="page-eyebrow">Step 01 · Ingest</div>
        <h1 class="page-title">Upload <em>Research Papers</em></h1>
        <p class="page-subtitle">
            Upload academic PDFs or DOCX files. EmpiricX will parse, chunk, and extract 
            structured empirical intelligence from each paper.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── API Key check ──────────────────────────────────────────────
    if not st.session_state.get("openai_api_key"):
        st.warning("⚠️  Enter your OpenAI API key in the sidebar before uploading papers.")

    # ── File uploader ──────────────────────────────────────────────
    st.markdown("#### Upload Papers")
    uploaded = st.file_uploader(
        "Drop PDF or DOCX files here",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Supported formats: PDF, DOCX, TXT. Max ~50MB per file.",
        label_visibility="collapsed"
    )

    if uploaded:
        st.markdown(f"**{len(uploaded)} file(s) selected:**")
        for f in uploaded:
            size_str = format_file_size(f.size)
            st.markdown(f"""
            <div class="paper-card">
                <span class="paper-icon">📄</span>
                <div>
                    <div class="paper-name">{f.name}</div>
                    <div class="paper-meta">{size_str} · {f.type or 'unknown'}</div>
                </div>
                <span class="paper-status status-ready">Ready</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            run_btn = st.button(
                f"⚡  Extract from {len(uploaded)} paper(s)",
                type="primary",
                use_container_width=True
            )

        with col2:
            if st.button("🗑  Clear All", use_container_width=True):
                st.session_state["extracted_papers"] = []
                st.session_state["synthesis_result"] = None
                st.session_state["processing_errors"] = []
                st.rerun()

        if run_btn:
            _process_files(uploaded)

    else:
        # Empty state
        st.markdown("""
        <div class="upload-zone">
            <span class="upload-icon">📂</span>
            <div class="upload-title">Drop your research papers here</div>
            <div class="upload-desc">PDF, DOCX, or TXT · Multiple files supported</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Already extracted papers summary ──────────────────────────
    existing = st.session_state.get("extracted_papers", [])
    errors = st.session_state.get("processing_errors", [])
    
    if existing:
        st.markdown("---")
        st.markdown(f"#### ✅ Extracted Papers ({len(existing)})")
        for p in existing:
            src = p.get("_source_file", "Unknown")
            author = p.get("author_year", "Unknown author")
            method = p.get("methodology", "—")
            st.markdown(f"""
            <div class="paper-card">
                <span class="paper-icon">✅</span>
                <div>
                    <div class="paper-name">{src}</div>
                    <div class="paper-meta">{author} · {method}</div>
                </div>
                <span class="paper-status status-ready">Extracted</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("")
        if st.button("📊  View Results →", type="primary"):
            st.session_state["page"] = "results"
            st.rerun()

    if errors:
        st.markdown("#### ⚠️ Processing Errors")
        for err in errors:
            st.error(err)


def _process_files(uploaded_files):
    """Process each uploaded file: parse → extract → save."""
    if not st.session_state.get("openai_api_key"):
        st.error("Please enter your OpenAI API key in the sidebar.")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = list(st.session_state.get("extracted_papers", []))
    errors = []
    
    # Track already-processed filenames to avoid duplicates
    existing_names = {p.get("_source_file") for p in results}

    total = len(uploaded_files)
    for i, file in enumerate(uploaded_files):
        if file.name in existing_names:
            status_text.markdown(f"⏭  Skipping `{file.name}` (already extracted)")
            progress_bar.progress((i + 1) / total)
            continue
        
        status_text.markdown(f"🔍  Parsing `{file.name}`...")
        progress_bar.progress(i / total)
        
        try:
            # 1. Extract raw text
            file_bytes = file.read()
            raw_text = extract_text(file_bytes, file.name)
            
            if len(raw_text.strip()) < 200:
                raise ValueError("Extracted text is too short — the file may be scanned/image-based.")

            # 2. Smart truncate for token limits
            text = smart_truncate(raw_text, max_tokens=12000)
            
            # 3. LLM extraction
            status_text.markdown(f"🧠  Extracting empirical data from `{file.name}`...")
            paper_data = extract_paper(text, filename=file.name)
            results.append(paper_data)
            
            status_text.markdown(f"✅  Done: `{file.name}`")
            
        except Exception as e:
            err_msg = f"**{file.name}**: {str(e)}"
            errors.append(err_msg)
            st.warning(f"⚠️ Skipped `{file.name}`: {e}")
        
        progress_bar.progress((i + 1) / total)

    progress_bar.progress(1.0)
    
    st.session_state["extracted_papers"] = results
    st.session_state["processing_errors"] = errors
    st.session_state["synthesis_result"] = None  # Reset synthesis when papers change

    if results:
        n_new = len(results) - (len(st.session_state.get("extracted_papers", [])) - len(results))
        status_text.markdown(f"✅  Extraction complete — {len(results)} paper(s) ready.")
        st.success(f"Successfully extracted {len(results)} paper(s). Navigate to **Extraction Results**.")
    else:
        status_text.markdown("❌ No papers were successfully extracted.")
