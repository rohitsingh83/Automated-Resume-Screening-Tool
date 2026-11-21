"""
The full pipeline in one place:

resume files -> text extraction -> cleaning -> parsing -> TF-IDF similarity
-> scoring -> ranking -> results table
"""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from .cleaner import clean_text, redact_pii
from .extractor import extract_text, extract_text_from_bytes, list_resumes
from .matcher import MatchResult, score_candidate, tfidf_similarities
from .parser import ParsedResume, load_skill_dictionary, parse_resume

JOBS_DIR = Path(__file__).resolve().parent.parent / "data" / "job_descriptions"


@dataclass
class Candidate:
    file: str
    parsed: ParsedResume
    match: MatchResult


def load_jobs(folder: Path = JOBS_DIR) -> dict[str, dict]:
    jobs = {}
    for path in sorted(folder.glob("*.json")):
        job = json.loads(path.read_text(encoding="utf-8"))
        jobs[job["id"]] = job
    return jobs


def job_text(job: dict) -> str:
    """Text used for similarity: description plus the skill lists."""
    return " ".join([job.get("title", ""), job.get("description", ""),
                     " ".join(job.get("must_have", [])), " ".join(job.get("nice_to_have", []))])


def screen_texts(job: dict, resumes: list[tuple[str, str]], weights: dict | None = None,
                 today: date | None = None) -> list[Candidate]:
    """resumes: list of (file name, raw text). Returns candidates ranked best first."""
    if not resumes:
        return []
    dictionary = load_skill_dictionary()
    parsed = [parse_resume(text, dictionary, today) for _, text in resumes]
    # PII is removed before vectorising so names/emails never influence the score.
    cleaned = [clean_text(redact_pii(text)) for _, text in resumes]
    sims = tfidf_similarities(clean_text(job_text(job)), cleaned)

    candidates = [Candidate(file=name, parsed=p, match=score_candidate(p, s, job, weights))
                  for (name, _), p, s in zip(resumes, parsed, sims)]
    return sorted(candidates, key=lambda c: c.match.score, reverse=True)


def screen_folder(job: dict, folder: str | Path, weights: dict | None = None,
                  today: date | None = None) -> list[Candidate]:
    resumes = [(p.name, extract_text(p)) for p in list_resumes(folder)]
    return screen_texts(job, resumes, weights, today)


def screen_uploads(job: dict, files: list[tuple[str, bytes]], weights: dict | None = None) -> list[Candidate]:
    resumes = [(name, extract_text_from_bytes(name, data)) for name, data in files]
    return screen_texts(job, resumes, weights)


def to_dataframe(candidates: list[Candidate]) -> pd.DataFrame:
    rows = []
    for rank, c in enumerate(candidates, start=1):
        m, p = c.match, c.parsed
        rows.append({
            "Rank": rank,
            "Candidate": p.name,
            "File": c.file,
            "Score": m.score,
            "Decision": m.decision,
            "Must-have %": round(100 * m.components["must_have"]),
            "Similarity %": round(100 * m.components["similarity"]),
            "Experience (yrs)": p.years_experience,
            "Education": (p.education or "-").title(),
            "Matched must-have": ", ".join(m.must_have_matched) or "-",
            "Missing must-have": ", ".join(m.must_have_missing) or "-",
            "Bonus skills": ", ".join(m.nice_to_have_matched) or "-",
            "All skills": ", ".join(sorted(p.skills)),
            "Flags": " | ".join(m.flags) or "-",
            "Email": p.email or "-",
        })
    return pd.DataFrame(rows)
