"""Text cleaning, PII redaction, skill extraction, experience, and education parsing."""

import re
from typing import Dict, List

SKILLS_DICTIONARY = [
    "python", "pandas", "numpy", "scikit-learn", "sql", "git", "fastapi",
    "nlp", "tf-idf", "docker", "streamlit", "regex", "rest api", "matplotlib",
    "seaborn", "tensorflow", "pytorch", "flask", "django", "java", "c++",
    "excel", "power bi", "tableau", "linux", "aws", "postgresql", "sqlite",
]

EDUCATION_PATTERNS = [
    r"\b(b\.?tech|b\.?e\.?|b\.?sc\.?|m\.?tech|m\.?sc\.?|bca|mca|ph\.?d\.?)\b",
]


def redact_pii(text: str) -> str:
    """Redact emails and phone numbers before ML scoring to reduce bias."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", text)
    text = re.sub(r"(\+?\d[\d\s\-]{8,14}\d)", "[PHONE]", text)
    return text


def clean_for_nlp(text: str) -> str:
    """Lowercase, redact PII, and strip non-alphanumeric punctuation."""
    text = redact_pii(text).lower()
    text = re.sub(r"[^a-z0-9\s\+\-\.]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_skills(text: str, vocabulary: List[str] = None) -> List[str]:
    """Match curated skills against resume text using word-boundary regex."""
    vocab = vocabulary or SKILLS_DICTIONARY
    lowered = text.lower()
    found = []
    for skill in vocab:
        pattern = r"(?<![a-z0-9])" + re.escape(skill.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, lowered):
            found.append(skill.lower())
    return sorted(set(found))


def extract_years_experience(text: str) -> float:
    """Extract numeric years of experience from common resume phrasings."""
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", text.lower())
    if not matches:
        if "intern" in text.lower() or "internship" in text.lower():
            return 0.5
        return 0.0
    return max(float(m) for m in matches)


def extract_education(text: str) -> str:
    """Identify highest/first matched degree keyword."""
    for pat in EDUCATION_PATTERNS:
        m = re.search(pat, text.lower())
        if m:
            return m.group(1).upper()
    return "Not Specified"


def parse_resume(clean_text: str) -> Dict:
    """Return structured candidate profile without PII."""
    return {
        "nlp_text": clean_for_nlp(clean_text),
        "skills": extract_skills(clean_text),
        "years_experience": extract_years_experience(clean_text),
        "education": extract_education(clean_text),
    }
