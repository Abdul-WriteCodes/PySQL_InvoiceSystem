"""
SLR Analyser — Systematic Literature Review Tool
Uses OpenAI GPT-4o-mini to abstract papers, identify themes, and write synthesis.
"""

import streamlit as st
from openai import OpenAI
import json, time, zipfile, io, csv
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="SLR Analyser", page_icon="🔬", layout="wide")

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE — initialise ALL keys up front, once
# ─────────────────────────────────────────────────────────────────────────────
if "initialised" not in st.session_state:
    st.session_state.initialised    = True
    st.session_state.api_key        = ""
    st.session_state.files          = {}       # {filename: bytes}
    st.session_state.abstractions   = []       # list of dicts
    st.session_state.themes         = ""
    st.session_state.synthesis      = ""
    st.session_state.stage          = "upload" # upload|abstract|themes|results
    st.session_state.abs_done       = False
    st.session_state.themes_done    = False

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0f172a,#1e293b);border-right:1px solid #334155;}
[data-testid="stSidebar"] *{color:#e2e8f0 !important;}
.hdr{background:linear-gradient(135deg,#1e3a5f,#1e40af,#1d4ed8);border-radius:16px;
     padding:2rem 2.5rem;margin-bottom:1.5rem;box-shadow:0 4px 24px rgba(30,64,175,.25);}
.hdr h1{color:#f0f9ff;font-size:2rem;font-weight:700;margin:0;}
.hdr p{color:#bae6fd;margin:.4rem 0 0;}
.pill{display:inline-block;padding:5px 14px;border-radius:20px;font-size:.8rem;font-weight:600;margin:2px;}
.pill.done{background:#dcfce7;color:#166534;}
.pill.active{background:#dbeafe;color:#1e40af;}
.pill.pending{background:#f1f5f9;color:#94a3b8;}
.ok{background:#f0fdf4;border:1.5px solid #86efac;border-radius:10px;
    padding:.8rem 1rem;color:#166534;margin-bottom:1rem;}
.hint{background:#eff6ff;border:1.5px solid #93c5fd;border-radius:10px;
      padding:.8rem 1rem;color:#1e40af;margin-bottom:1rem;}
.chip{display:inline-flex;align-items:center;gap:6px;background:#f8fafc;
      border:1px solid #e2e8f0;border-radius:8px;padding:5px 10px;
      font-size:.8rem;color:#334155;margin:3px;}
.chip small{color:#94a3b8;}
.badge{display:inline-block;background:#dbeafe;color:#1e40af;border-radius:6px;
       padding:2px 8px;font-size:.75rem;font-weight:600;margin:2px;}
.badge.g{background:#dcfce7;color:#166534;}
.badge.p{background:#f3e8ff;color:#6b21a8;}
.badge.a{background:#fef3c7;color:#92400e;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
SUPPORTED = {".pdf", ".docx", ".doc", ".txt"}

def ingest_uploads(widget_key: str):
    """
    Callback: called by file_uploader on_change.
    Reads bytes from every uploaded file and stores in session_state.files.
    Running inside a callback means the widget value is stable — no rerun race.
    """
    uploads = st.session_state.get(widget_key) or []
    store = {}
    for f in uploads:
        raw = f.getvalue()
        name = f.name
        if name.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                    for member in zf.namelist():
                        if member.endswith("/") or "__MACOSX" in member:
                            continue
                        if Path(member).suffix.lower() not in SUPPORTED:
                            continue
                        nm = Path(member).name
                        if nm not in store:
                            store[nm] = zf.read(member)
            except Exception as e:
                st.warning(f"ZIP error ({name}): {e}")
        else:
            store[name] = raw
    st.session_state.files = store

def extract_text(name: str, data: bytes) -> str:
    ext = Path(name).suffix.lower()
    if ext == ".pdf":
        try:
            import pypdf
            r = pypdf.PdfReader(io.BytesIO(data))
            txt = "\n\n".join(p.extract_text() or "" for p in r.pages).strip()
            return txt or "[PDF has no extractable text]"
        except Exception as e:
            return f"[PDF error: {e}]"
    if ext in (".docx", ".doc"):
        try:
            import docx
            d = docx.Document(io.BytesIO(data))
            return "\n\n".join(p.text for p in d.paragraphs if p.text.strip())
        except Exception as e:
            return f"[DOCX error: {e}]"
    return data.decode("utf-8", errors="replace")

def call_gpt(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    client = OpenAI(api_key=st.session_state.api_key)
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    r = client.chat.completions.create(
        model="gpt-4o-mini", max_tokens=max_tokens,
        temperature=0.2, messages=msgs)
    return r.choices[0].message.content.strip()

def abstract_paper(name: str, text: str) -> dict:
    sys = ("You are an expert SLR assistant. Extract metadata from academic papers. "
           "Respond with raw JSON only — no markdown fences, no extra text.")
    prompt = f"""Extract these fields. Use null for unknown values.
Return ONLY a raw JSON object with keys:
  title, authors (list), year, journal_or_venue,
  methodology_design, sample_size,
  main_findings (2-4 sentences),
  contributions (1-3 key points as one string),
  limitations, keywords (list up to 8)

FILENAME: {name}
TEXT (first 6000 chars):
{text[:6000]}"""
    raw = call_gpt(prompt, sys, 1200).strip()
    # Strip accidental fences
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1][4:].strip() if parts[1].startswith("json") else parts[1].strip()
    try:
        d = json.loads(raw)
    except Exception:
        d = {"title": name, "authors": [], "year": None, "journal_or_venue": None,
             "methodology_design": "Unknown", "sample_size": None,
             "main_findings": raw[:400], "contributions": "",
             "limitations": None, "keywords": []}
    if not d.get("title") or str(d.get("title")).lower() == "null":
        d["title"] = name
    return d

def run_themes(abstractions: list) -> str:
    sys = "You are an expert systematic review analyst."
    parts = []
    for i, p in enumerate(abstractions, 1):
        parts.append(f"Paper {i}: {p.get('title')}\n"
                     f"  Year:{p.get('year')} | Method:{p.get('methodology_design')}\n"
                     f"  Findings:{p.get('main_findings')}\n"
                     f"  Keywords:{', '.join(p.get('keywords') or [])}")
    prompt = f"""Thematic synthesis across {len(abstractions)} academic papers:

{chr(10).join(parts)}

Tasks:
1. Identify 4-7 major cross-cutting themes (cite papers by number).
2. Per theme: clear title, 3-5 sentence explanation, note contradictions/gaps.
3. Concluding paragraph on research trajectory and future directions.

Use ## markdown headings per theme. Clean academic markdown."""
    return call_gpt(prompt, sys, 3000)

def run_synthesis(abstractions: list, themes_txt: str) -> str:
    sys = "You are an expert academic writer specialising in systematic literature reviews."
    years = sorted({str(p.get("year")) for p in abstractions if p.get("year")})
    prompt = f"""Write a comprehensive Discussion / Synthesis section (600-900 words).

Corpus: {len(abstractions)} papers | Years: {', '.join(years) or 'N/A'}

THEMATIC ANALYSIS:
{themes_txt}

Include:
- Opening paragraph contextualising the literature
- A paragraph per major theme weaving evidence from multiple papers
- Methodological diversity and cross-study limitations
- Concluding paragraph: implications and research gaps

Formal academic prose. No first person. Use markdown formatting."""
    return call_gpt(prompt, sys, 3000)

def build_export_zip(abstractions, themes, synthesis) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("abstractions.json", json.dumps(abstractions, indent=2))
        zf.writestr("themes.md", themes or "")
        zf.writestr("synthesis.md", synthesis or "")
        csv_buf = io.StringIO()
        fields = ["title","authors","year","journal_or_venue","methodology_design",
                  "sample_size","main_findings","contributions","limitations","keywords"]
        w = csv.DictWriter(csv_buf, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for p in abstractions:
            w.writerow({k: (", ".join(v) if isinstance(v, list) else (v or ""))
                        for k, v in p.items()})
        zf.writestr("summary_table.csv", csv_buf.getvalue())
    return buf.getvalue()

def stage_index(s):
    return {"upload": 0, "abstract": 1, "themes": 2, "results": 3}[s]

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔬 SLR Analyser")
    st.markdown("---")

    key_val = st.text_input("OpenAI API Key", type="password",
                            value=st.session_state.api_key,
                            placeholder="sk-...",
                            label_visibility="visible")
    if key_val != st.session_state.api_key:
        st.session_state.api_key = key_val

    if st.session_state.api_key:
        st.success("✅ API key ready")
    else:
        st.warning("⚠️ Enter API key to enable analysis")

    st.markdown("---")
    if st.session_state.files:
        st.markdown(f"**📁 {len(st.session_state.files)} file(s) loaded**")
        for nm, data in st.session_state.files.items():
            st.markdown(
                f'<div class="chip">📄 {nm} <small>{len(data)//1024} KB</small></div>',
                unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Formats:** `.pdf` `.docx` `.txt` `.zip`")
    st.markdown("**Model:** `gpt-4o-mini`")
    st.markdown("---")
    if st.button("🔄 Reset Everything", use_container_width=True):
        st.session_state.files        = {}
        st.session_state.abstractions = []
        st.session_state.themes       = ""
        st.session_state.synthesis    = ""
        st.session_state.stage        = "upload"
        st.session_state.abs_done     = False
        st.session_state.themes_done  = False
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">
  <h1>🔬 Systematic Literature Review Analyser</h1>
  <p>Upload papers → Extract structured data → Identify themes → Generate synthesis</p>
</div>""", unsafe_allow_html=True)

# Progress pills
cur_idx = stage_index(st.session_state.stage)
STAGES  = [("upload","📤 Upload"), ("abstract","🔍 Abstract"),
           ("themes","🧵 Themes"), ("results","✅ Results")]
pills = ""
for i, (_, label) in enumerate(STAGES):
    cls = "done" if i < cur_idx else ("active" if i == cur_idx else "pending")
    pills += f'<span class="pill {cls}">{label}</span>'
    if i < len(STAGES)-1:
        pills += ' <span style="color:#cbd5e1">›</span> '
st.markdown(pills, unsafe_allow_html=True)
st.markdown("")

# ─────────────────────────────────────────────────────────────────────────────
# ══ STAGE: UPLOAD ══
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.stage == "upload":
    st.markdown("### 📤 Step 1 — Upload Your Papers")
    st.caption("PDF · DOCX · TXT · ZIP bundle · Multiple files at once")

    # The on_change callback fires BEFORE the rerun, so bytes are captured safely
    st.file_uploader(
        "Drop files here",
        type=["pdf", "docx", "txt", "zip"],
        accept_multiple_files=True,
        key="uploader_widget",
        on_change=ingest_uploads,
        args=("uploader_widget",),
        label_visibility="collapsed",
    )

    # Always read from session_state.files — not from the widget
    if st.session_state.files:
        n = len(st.session_state.files)
        st.markdown(
            f'<div class="ok">✅ <strong>{n} file(s) loaded and ready for analysis</strong></div>',
            unsafe_allow_html=True)

        chips = "".join(
            f'<span class="chip">📄 {nm} <small>{len(d)//1024} KB · {Path(nm).suffix.upper()[1:]}</small></span>'
            for nm, d in st.session_state.files.items()
        )
        st.markdown(chips, unsafe_allow_html=True)
        st.markdown("")

        if not st.session_state.api_key:
            st.warning("⚠️ Add your OpenAI API key in the sidebar to continue.")
        else:
            st.markdown(
                '<div class="hint">👇 Click <strong>Analyse Documents</strong> to begin data extraction.</div>',
                unsafe_allow_html=True)
            if st.button("🚀 Analyse Documents", type="primary", use_container_width=False):
                st.session_state.stage    = "abstract"
                st.session_state.abs_done = False
                st.rerun()
    else:
        st.markdown("""
        <div style="border:2px dashed #cbd5e1;border-radius:14px;padding:3rem;
                    text-align:center;color:#94a3b8;margin-top:.5rem">
            <div style="font-size:3rem">📂</div>
            <div style="font-weight:600;margin-top:.5rem">
                Drag & drop files above, or click Browse</div>
            <div style="font-size:.85rem;margin-top:.3rem">
                PDF · DOCX · TXT · ZIP (batch) · multiple files at once</div>
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ══ STAGE: ABSTRACT ══
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.stage == "abstract":
    st.markdown("### 🔍 Step 2 — Data Abstraction")

    if not st.session_state.files:
        st.error("No files found. Please go back and upload papers first.")
        if st.button("← Back to Upload"):
            st.session_state.stage = "upload"
            st.rerun()
        st.stop()

    # ── Already done: show results + next step button
    if st.session_state.abs_done and st.session_state.abstractions:
        abs_list = st.session_state.abstractions
        st.markdown(
            f'<div class="ok">✅ <strong>Data abstraction complete — {len(abs_list)} paper(s) processed.</strong></div>',
            unsafe_allow_html=True)

        import pandas as pd
        rows = [{"#": i+1,
                 "Title":  p.get("title","")[:55],
                 "Year":   p.get("year") or "?",
                 "Method": p.get("methodology_design") or "?",
                 "1st Author": (p.get("authors") or ["?"])[0]}
                for i, p in enumerate(abs_list)]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

        with st.expander("🔎 View detailed abstractions for all papers"):
            for p in abs_list:
                st.markdown(f"#### 📄 {p.get('title','Untitled')}")
                c1, c2 = st.columns([3, 1])
                with c1:
                    if p.get("authors"):
                        st.markdown(f"**Authors:** {', '.join(p['authors'][:5])}")
                    st.markdown(f"**Journal/Venue:** {p.get('journal_or_venue') or '_N/A_'}")
                    st.markdown(f"**Main Findings:** {p.get('main_findings') or '_N/A_'}")
                    st.markdown(f"**Contributions:** {p.get('contributions') or '_N/A_'}")
                    if p.get("limitations"):
                        st.markdown(f"**Limitations:** {p['limitations']}")
                with c2:
                    b = ""
                    if p.get("year"):
                        b += f'<span class="badge a">{p["year"]}</span> '
                    if p.get("methodology_design"):
                        b += f'<span class="badge p">{p["methodology_design"]}</span> '
                    if p.get("sample_size"):
                        b += f'<span class="badge g">n={p["sample_size"]}</span>'
                    if b:
                        st.markdown(b, unsafe_allow_html=True)
                    kws = p.get("keywords") or []
                    if kws:
                        st.markdown(
                            " ".join(f'<span class="badge">{k}</span>' for k in kws),
                            unsafe_allow_html=True)
                st.markdown("---")

        st.markdown(
            '<div class="hint">👇 Click <strong>Find Key Themes</strong> to identify cross-cutting themes across all papers.</div>',
            unsafe_allow_html=True)
        col1, col2 = st.columns([2, 5])
        with col1:
            if st.button("🧵 Find Key Themes & Write Discussion", type="primary", use_container_width=True):
                st.session_state.stage       = "themes"
                st.session_state.themes_done = False
                st.rerun()
        with col2:
            if st.button("← Back to Upload"):
                st.session_state.stage    = "upload"
                st.session_state.abs_done = False
                st.rerun()

    # ── Not done yet: run abstraction
    else:
        files    = st.session_state.files
        names    = list(files.keys())
        n        = len(names)
        st.markdown(
            f'<div class="hint">⏳ Extracting structured data from <strong>{n} paper(s)</strong> using GPT-4o-mini…</div>',
            unsafe_allow_html=True)

        prog      = st.progress(0)
        status    = st.empty()
        results   = []

        for i, nm in enumerate(names):
            status.markdown(f"**Processing ({i+1}/{n}):** `{nm}`")
            prog.progress(i / n)
            txt = extract_text(nm, files[nm])
            if txt.startswith("["):
                st.warning(f"⚠️ `{nm}`: {txt}")
            try:
                d = abstract_paper(nm, txt)
            except Exception as e:
                st.warning(f"⚠️ Failed on `{nm}`: {e}")
                d = {"title": nm, "authors": [], "year": None, "journal_or_venue": None,
                     "methodology_design": "Error", "sample_size": None,
                     "main_findings": f"Error: {e}", "contributions": "",
                     "limitations": None, "keywords": []}
            results.append(d)

        prog.progress(1.0)
        status.success(f"✅ Done — {len(results)} paper(s) abstracted successfully!")

        # Persist results, then rerun to show the "done" view
        st.session_state.abstractions = results
        st.session_state.abs_done     = True
        time.sleep(0.8)
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# ══ STAGE: THEMES ══
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.stage == "themes":
    st.markdown("### 🧵 Step 3 — Key Themes & Discussion")

    if not st.session_state.abs_done or not st.session_state.abstractions:
        st.error("No abstraction data found. Please complete Step 2 first.")
        if st.button("← Back to Abstraction"):
            st.session_state.stage = "abstract"
            st.rerun()
        st.stop()

    # ── Already done
    if st.session_state.themes_done and st.session_state.themes:
        st.markdown(
            '<div class="ok">✅ <strong>Theme identification and synthesis complete.</strong></div>',
            unsafe_allow_html=True)

        t1, t2 = st.tabs(["🧵 Key Themes", "✍️ Discussion / Synthesis"])
        with t1:
            st.markdown(st.session_state.themes)
        with t2:
            st.markdown(st.session_state.synthesis)

        st.markdown(
            '<div class="hint">👇 Click <strong>View Full Results</strong> to see all abstractions, the summary table, and download your package.</div>',
            unsafe_allow_html=True)
        col1, col2 = st.columns([2, 5])
        with col1:
            if st.button("📊 View Full Results & Export", type="primary", use_container_width=True):
                st.session_state.stage = "results"
                st.rerun()
        with col2:
            if st.button("← Back to Abstraction"):
                st.session_state.stage = "abstract"
                st.rerun()

    # ── Run it
    else:
        abstractions = st.session_state.abstractions
        st.markdown(
            f'<div class="hint">⏳ Analysing <strong>{len(abstractions)} paper(s)</strong> — identifying themes and writing discussion…</div>',
            unsafe_allow_html=True)

        with st.spinner("🧵 Identifying cross-cutting themes…"):
            try:
                themes = run_themes(abstractions)
                st.session_state.themes = themes
            except Exception as e:
                st.error(f"Theme identification failed: {e}")
                st.stop()

        with st.spinner("✍️ Writing academic synthesis / discussion…"):
            try:
                synthesis = run_synthesis(abstractions, st.session_state.themes)
                st.session_state.synthesis = synthesis
            except Exception as e:
                st.error(f"Synthesis writing failed: {e}")
                st.stop()

        st.session_state.themes_done = True
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# ══ STAGE: RESULTS ══
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.stage == "results":
    abstractions = st.session_state.abstractions
    themes       = st.session_state.themes
    synthesis    = st.session_state.synthesis

    years   = [p.get("year") for p in abstractions if p.get("year")]
    methods = [p.get("methodology_design","") for p in abstractions]
    kws     = [k for p in abstractions for k in (p.get("keywords") or [])]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📄 Papers",          len(abstractions))
    m2.metric("📅 Year Range",      f"{min(years)}–{max(years)}" if years else "N/A")
    m3.metric("🧪 Study Designs",   len({m for m in methods if m not in ("","Unknown","Error")}))
    m4.metric("🔑 Unique Keywords", len(set(kws)))
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📑 All Abstractions", "🧵 Key Themes",
        "✍️ Discussion",        "📊 Summary Table"])

    with tab1:
        st.markdown(f"#### {len(abstractions)} Paper Abstractions")
        for p in abstractions:
            with st.expander(f"📄 {p.get('title','Untitled')}"):
                c1, c2 = st.columns([3, 1])
                with c1:
                    if p.get("authors"):
                        st.markdown(f"**Authors:** {', '.join(p['authors'][:5])}")
                    st.markdown(f"**Journal/Venue:** {p.get('journal_or_venue') or '_N/A_'}")
                    st.markdown(f"**Main Findings:** {p.get('main_findings') or '_N/A_'}")
                    st.markdown(f"**Contributions:** {p.get('contributions') or '_N/A_'}")
                    if p.get("limitations"):
                        st.markdown(f"**Limitations:** {p['limitations']}")
                with c2:
                    b = ""
                    if p.get("year"): b += f'<span class="badge a">{p["year"]}</span> '
                    if p.get("methodology_design"): b += f'<span class="badge p">{p["methodology_design"]}</span> '
                    if p.get("sample_size"): b += f'<span class="badge g">n={p["sample_size"]}</span>'
                    if b: st.markdown(b, unsafe_allow_html=True)
                    kw_list = p.get("keywords") or []
                    if kw_list:
                        st.markdown(" ".join(f'<span class="badge">{k}</span>' for k in kw_list),
                                    unsafe_allow_html=True)

    with tab2:
        st.markdown(themes or "_No themes generated._")

    with tab3:
        st.markdown(synthesis or "_No synthesis generated._")

    with tab4:
        import pandas as pd
        rows = []
        for p in abstractions:
            t = p.get("title","")
            rows.append({
                "Title":        t[:60] + ("…" if len(t)>60 else ""),
                "Year":         p.get("year") or "?",
                "Method":       p.get("methodology_design") or "?",
                "First Author": (p.get("authors") or ["?"])[0],
                "Venue":        (p.get("journal_or_venue") or "?")[:40],
                "Keywords":     ", ".join((p.get("keywords") or [])[:4]),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 📦 Download Results")
    col1, col2 = st.columns([1, 3])
    with col1:
        st.download_button(
            "⬇️ Download Full Package (.zip)",
            data=build_export_zip(abstractions, themes, synthesis),
            file_name="slr_results.zip",
            mime="application/zip",
            use_container_width=True)
    with col2:
        st.caption("Contains: `abstractions.json` · `summary_table.csv` · `themes.md` · `synthesis.md`")
    st.markdown("")
    if st.button("← Back to Themes & Discussion"):
        st.session_state.stage = "themes"
        st.rerun()
