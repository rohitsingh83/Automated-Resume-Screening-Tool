"""Resume and Job Description ingestion module (PDF, DOCX, TXT)."""

import re
from pathlib import Path
from typing import Dict, List

from docx import Document
from pypdf import PdfReader


def normalize_whitespace(text: str) -> str:
    """Collapse excessive whitespace while preserving readable structure."""
    return re.sub(r"\s+", " ", text).strip()


def extract_text_from_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_text_from_docx(path: Path) -> str:
    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" ".join(cell.text.strip() for cell in row.cells if cell.text.strip()))
    return "\n".join(parts)


def extract_text_from_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def load_resume(path: Path) -> Dict[str, str]:
    """Load a single resume file (.txt, .docx, .pdf) and return normalized text."""
    ext = path.suffix.lower()
    if ext == ".txt":
        raw = extract_text_from_txt(path)
    elif ext == ".docx":
        raw = extract_text_from_docx(path)
    elif ext == ".pdf":
        raw = extract_text_from_pdf(path)
    else:
        raise ValueError(f"Unsupported resume format: {ext}")

    return {
        "filename": path.name,
        "candidate_name": path.stem.replace("_", " ").title(),
        "raw_text": raw,
        "clean_text": normalize_whitespace(raw),
    }


def load_all_resumes(resumes_dir: Path) -> List[Dict[str, str]]:
    """Ingest all supported resumes from a directory."""
    supported = {".txt", ".docx", ".pdf"}
    results = []
    for p in sorted(resumes_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in supported:
            results.append(load_resume(p))
    return results
