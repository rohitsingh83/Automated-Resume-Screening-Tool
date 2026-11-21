"""
Step 1 of the pipeline: get plain text out of a resume file.

Supported formats:
  .pdf   -> pdfplumber (reads the text layer page by page)
  .docx  -> python-docx (paragraphs + tables)
  .txt   -> read as UTF-8
"""

from io import BytesIO
from pathlib import Path

import pdfplumber
from docx import Document

SUPPORTED = {".pdf", ".docx", ".txt"}


def extract_pdf(data: bytes) -> str:
    pages = []
    with pdfplumber.open(BytesIO(data)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages)


def extract_docx(data: bytes) -> str:
    doc = Document(BytesIO(data))
    parts = [p.text for p in doc.paragraphs]
    # Many resumes put skills inside tables, so read those too.
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(parts)


def extract_text_from_bytes(filename: str, data: bytes) -> str:
    """Extract text from an uploaded file (used by the Streamlit app and API)."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return extract_pdf(data)
    if suffix == ".docx":
        return extract_docx(data)
    if suffix == ".txt":
        return data.decode("utf-8", errors="ignore")
    raise ValueError(f"Unsupported file type '{suffix}'. Use PDF, DOCX or TXT.")


def extract_text(path: str | Path) -> str:
    """Extract text from a resume file on disk."""
    path = Path(path)
    return extract_text_from_bytes(path.name, path.read_bytes())


def list_resumes(folder: str | Path) -> list[Path]:
    """All supported resume files in a folder, sorted by name."""
    return sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in SUPPORTED)
