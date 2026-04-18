import io
import re
from typing import Optional


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        chunks = []
        for page in doc:
            text = page.get_text("text")
            if text.strip():
                chunks.append(text)
        doc.close()
        return "\n\n".join(chunks)
    except Exception as e:
        raise RuntimeError(f"PDF parsing failed: {e}")


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        raise RuntimeError(f"DOCX parsing failed: {e}")


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Auto-detect file type and extract text."""
    name_lower = filename.lower()
    if name_lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif name_lower.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    elif name_lower.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"Unsupported file type: {filename}")


def smart_truncate(text: str, max_tokens: int = 12000) -> str:
    """
    Truncate text intelligently — prefer keeping abstract + methods + results.
    Rough heuristic: 1 token ≈ 4 chars.
    """
    max_chars = max_tokens * 4

    if len(text) <= max_chars:
        return text

    # Try to find key sections
    section_patterns = [
        r"(abstract[\s\S]{0,3000})",
        r"(introduction[\s\S]{0,2000})",
        r"(method(?:ology|s)?[\s\S]{0,4000})",
        r"(result[\s\S]{0,3000})",
        r"(discussion[\s\S]{0,2000})",
        r"(conclusion[\s\S]{0,2000})",
    ]

    found_sections = []
    text_lower = text.lower()
    for pattern in section_patterns:
        match = re.search(pattern, text_lower)
        if match:
            start, end = match.span()
            found_sections.append(text[start:end])

    if found_sections:
        combined = "\n\n".join(found_sections)
        if len(combined) > max_chars:
            return combined[:max_chars]
        return combined

    # Fallback: take beginning
    return text[:max_chars]


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024*1024):.1f} MB"
