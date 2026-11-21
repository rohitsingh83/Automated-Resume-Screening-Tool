"""
Step 3: turn resume text into structured information.

Extracts: name, email, phone, skills (using an alias dictionary),
years of experience (from date ranges such as "Jun 2022 - Present"),
and the highest education level.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .cleaner import EMAIL_RE, PHONE_RE, clean_text

SKILLS_FILE = Path(__file__).resolve().parent.parent / "data" / "skills.json"

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}

# Ordered from highest to lowest. The first level whose pattern matches wins.
EDUCATION_LEVELS = [
    ("phd", 4, r"\bph\.?\s?d\b|\bdoctorate\b"),
    ("master", 3, r"\bm\.?\s?tech\b|\bm\.?\s?e\.?(?=\s+in\b)|\bmba\b|\bm\.?\s?sc\b|\bmca\b|\bmaster'?s?\b"),
    ("bachelor", 2, r"\bb\.?\s?tech\b|\bb\.?\s?e\.?(?=\s+in\b)|\bb\.?\s?sc\b|\bbba\b|\bbca\b|\bb\.?\s?com\b|\bbachelor'?s?\b"),
    ("diploma", 1, r"\bdiploma\b"),
]
EDUCATION_RANK = {name: rank for name, rank, _ in EDUCATION_LEVELS}

SPECIAL_NAMES = {"sql": "SQL", "power bi": "Power BI", "aws": "AWS", "gcp": "GCP", "nlp": "NLP", "llm": "LLM",
                 "rest api": "REST API", "ci/cd": "CI/CD", "html/css": "HTML/CSS", "scikit-learn": "scikit-learn"}


def pretty(skill: str) -> str:
    return SPECIAL_NAMES.get(skill, skill.title())


def load_skill_dictionary(path: Path = SKILLS_FILE) -> dict[str, dict[str, list[str]]]:
    """{category: {canonical_skill: [aliases]}}"""
    return json.loads(path.read_text(encoding="utf-8"))


def _alias_pattern(alias: str) -> re.Pattern:
    # Word-boundary match that also works for skills like "c++" or "ci/cd".
    return re.compile(r"(?<![a-z0-9])" + re.escape(alias.lower()) + r"(?![a-z0-9+#])")


@dataclass
class ParsedResume:
    name: str
    email: str | None
    phone: str | None
    skills: dict[str, int] = field(default_factory=dict)   # canonical skill -> mentions
    skill_categories: dict[str, list[str]] = field(default_factory=dict)
    years_experience: float = 0.0
    education: str | None = None
    word_count: int = 0


def extract_name(text: str) -> str:
    """The first short line made only of letters is usually the candidate's name."""
    for line in text.splitlines()[:5]:
        line = line.strip()
        if 2 <= len(line.split()) <= 4 and re.fullmatch(r"[A-Za-z .'-]+", line):
            return line.title()
    return "Unknown"


def extract_skills(clean: str, dictionary: dict) -> tuple[dict[str, int], dict[str, list[str]]]:
    found: dict[str, int] = {}
    by_category: dict[str, list[str]] = {}
    for category, skills in dictionary.items():
        for skill, aliases in skills.items():
            count = sum(len(_alias_pattern(a).findall(clean)) for a in aliases)
            if count:
                found[skill] = count
                by_category.setdefault(category, []).append(skill)
    return found, by_category


def _to_month_index(month: str | None, year: str) -> int:
    m = MONTHS.get(month[:3].lower(), 1) if month else 1
    return int(year) * 12 + (m - 1)


def extract_experience_years(text: str, today: date | None = None) -> float:
    """
    Add up work periods such as "Jun 2022 - Present" or "2019 - 2021".
    Overlapping periods are merged so parallel jobs are not double-counted.
    Falls back to phrases like "3+ years of experience".
    """
    today = today or date.today()
    now = today.year * 12 + today.month - 1
    month = r"(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
    pattern = re.compile(
        rf"(?:{month}\s+)?((?:19|20)\d{{2}})\s*(?:-|–|to)\s*(?:(present|current|now|till date)|(?:{month}\s+)?((?:19|20)\d{{2}}))",
        re.IGNORECASE)
    periods = []
    for m in pattern.finditer(text):
        start = _to_month_index(m.group(1), m.group(2))
        end = now if m.group(3) else _to_month_index(m.group(4), m.group(5)) + (0 if m.group(4) else 11)
        if 0 <= end - start <= 50 * 12:
            periods.append((start, min(end, now)))

    if periods:
        periods.sort()
        merged = [list(periods[0])]
        for s, e in periods[1:]:
            if s <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e)
            else:
                merged.append([s, e])
        months = sum(e - s + 1 for s, e in merged)
        return round(months / 12, 1)

    explicit = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)", text.lower())
    return max((float(x) for x in explicit), default=0.0)


def extract_education(text: str) -> str | None:
    low = text.lower()
    for name, _, pattern in EDUCATION_LEVELS:
        if re.search(pattern, low):
            return name
    return None


def _experience_section(text: str) -> str:
    """Only count dates inside the experience section (a line that is just the heading)."""
    heading = re.compile(r"^\s*(work experience|professional experience|experience|employment history)\s*:?\s*$",
                         re.IGNORECASE | re.MULTILINE)
    start = heading.search(text)
    if not start:
        return text
    rest = text[start.end():]
    end = re.search(r"^\s*(education|projects|certifications|skills|achievements)\b", rest,
                    re.IGNORECASE | re.MULTILINE)
    return rest[: end.start()] if end else rest


def parse_resume(text: str, dictionary: dict | None = None, today: date | None = None) -> ParsedResume:
    dictionary = dictionary or load_skill_dictionary()
    clean = clean_text(text)
    skills, categories = extract_skills(clean, dictionary)
    email = EMAIL_RE.search(text)
    phone = PHONE_RE.search(text)
    return ParsedResume(
        name=extract_name(text),
        email=email.group(0) if email else None,
        phone=phone.group(0).strip() if phone else None,
        skills=skills,
        skill_categories=categories,
        years_experience=extract_experience_years(_experience_section(text), today),
        education=extract_education(text),
        word_count=len(clean.split()),
    )
