"""Text cleaning, PII redaction, skill extraction, experience, and education parsing."""

import re
from typing import Dict, List, Optional

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
    """Redact emails and phone numbers before ML scoring to protect candidate privacy.
    
    Args:
        text: Raw resume text.
        
    Returns:
        Text with emails and phone numbers replaced with tokens.
    """
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", text)
    text = re.sub(r"(\+?\d[\d\s\-]{8,14}\d)", "[PHONE]", text)
    return text


def clean_for_nlp(text: str) -> str:
    """Lowercase, redact PII, and strip non-alphanumeric punctuation.
    
    Args:
        text: Raw text string.
        
    Returns:
        Normalized text suitable for NLP tokenization.
    """
    text = redact_pii(text).lower()
    text = re.sub(r"[^a-z0-9\s\+\-\.]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_skills(text: str, vocabulary: Optional[List[str]] = None) -> List[str]:
    """Match curated skills against resume text using word-boundary regex.
    
    Args:
        text: Cleaned resume text.
        vocabulary: Optional custom skill vocabulary.
        
    Returns:
        Sorted list of matched skill identifiers.
    """
    vocab = vocabulary or SKILLS_DICTIONARY
    lowered = text.lower()
    found = []
    for skill in vocab:
        pattern = r"(?<![a-z0-9])" + re.escape(skill.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, lowered):
            found.append(skill.lower())
    return sorted(set(found))


def extract_years_experience(text: str) -> float:
    """Extract and aggregate numerical years of experience from resume texts.
    
    Args:
        text: Resume content string.
        
    Returns:
        Estimated total years of professional experience.
    """
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)", text.lower())
    if not matches:
        if "intern" in text.lower() or "internship" in text.lower():
            return 0.5
        return 0.0
    
    # Filter out unreasonable single match numbers (>40 is usually phone/postal artifact)
    valid_numbers = [float(m) for m in matches if float(m) <= 40.0]
    if not valid_numbers:
        return 0.0
    
    return max(valid_numbers)


def extract_education(text: str) -> str:
    """Identify highest matched degree keyword.
    
    Args:
        text: Resume content string.
        
    Returns:
        Uppercase degree credential or 'Not Specified'.
    """
    for pat in EDUCATION_PATTERNS:
        m = re.search(pat, text.lower())
        if m:
            return m.group(1).upper()
    return "Not Specified"


def parse_resume(clean_text: str, vocabulary: Optional[List[str]] = None) -> Dict:
    """Return structured candidate profile without PII."""
    return {
        "nlp_text": clean_for_nlp(clean_text),
        "skills": extract_skills(clean_text, vocabulary=vocabulary),
        "years_experience": extract_years_experience(clean_text),
        "education": extract_education(clean_text),
    }
