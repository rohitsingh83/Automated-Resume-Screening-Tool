"""
Step 4: compare each resume with the job description and calculate a score.

The final score (0-100) is a weighted mix of five explainable parts:

    Component            Weight  How it is measured
    -------------------  ------  ---------------------------------------------
    Must-have skills      40%    share of required skills found in the resume
    Content similarity    25%    TF-IDF cosine similarity (resume vs JD text)
    Experience            15%    candidate years / required years (capped at 1)
    Nice-to-have skills   15%    share of bonus skills found
    Education              5%    meets the required degree level?

A penalty is applied when a resume looks keyword-stuffed (the same skill
repeated many times with little real content), a common trick to fool ATS.
"""

from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .parser import EDUCATION_RANK, ParsedResume, pretty

DEFAULT_WEIGHTS = {
    "must_have": 0.40,
    "similarity": 0.25,
    "experience": 0.15,
    "nice_to_have": 0.15,
    "education": 0.05,
}

# TF-IDF similarity between two *different* documents is rarely above ~0.45,
# so we rescale it to a 0-1 range before weighting.
SIMILARITY_CEILING = 0.45
SHORTLIST_SCORE = 65
REVIEW_SCORE = 45
MIN_MUST_HAVE_FOR_SHORTLIST = 0.8


@dataclass
class MatchResult:
    similarity: float
    must_have_matched: list[str]
    must_have_missing: list[str]
    nice_to_have_matched: list[str]
    components: dict[str, float]          # each component on a 0-1 scale
    score: float                          # 0-100
    decision: str                         # Shortlisted / Review / Rejected
    flags: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def tfidf_similarities(job_text: str, resume_texts: list[str]) -> list[float]:
    """Cosine similarity of every resume to the job description."""
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    matrix = vectorizer.fit_transform([job_text] + resume_texts)
    return cosine_similarity(matrix[0:1], matrix[1:]).flatten().tolist()


def keyword_stuffing_ratio(parsed: ParsedResume) -> float:
    """Skill mentions per 100 words. Genuine resumes in our tests sit between 8 and 30."""
    mentions = sum(parsed.skills.values())
    return 100 * mentions / max(parsed.word_count, 1)


def average_repetition(parsed: ParsedResume) -> float:
    """How many times each skill is mentioned on average. Genuine resumes: 1.5-2.7."""
    return sum(parsed.skills.values()) / max(len(parsed.skills), 1)


def looks_keyword_stuffed(parsed: ParsedResume) -> bool:
    # Both signals must fire: very dense skill words AND the same words repeated.
    return keyword_stuffing_ratio(parsed) > 35 and average_repetition(parsed) > 3.0


def score_candidate(parsed: ParsedResume, similarity: float, job: dict,
                    weights: dict | None = None) -> MatchResult:
    weights = weights or DEFAULT_WEIGHTS
    must = [s.lower() for s in job.get("must_have", [])]
    nice = [s.lower() for s in job.get("nice_to_have", [])]
    have = set(parsed.skills)

    must_hit = [s for s in must if s in have]
    must_miss = [s for s in must if s not in have]
    nice_hit = [s for s in nice if s in have]

    min_exp = float(job.get("min_experience", 0) or 0)
    required_edu = EDUCATION_RANK.get(job.get("education") or "", 0)
    candidate_edu = EDUCATION_RANK.get(parsed.education or "", 0)

    components = {
        "must_have": len(must_hit) / len(must) if must else 1.0,
        "similarity": min(similarity / SIMILARITY_CEILING, 1.0),
        "experience": min(parsed.years_experience / min_exp, 1.0) if min_exp else 1.0,
        "nice_to_have": len(nice_hit) / len(nice) if nice else 1.0,
        "education": 1.0 if candidate_edu >= required_edu else (0.5 if candidate_edu else 0.0),
    }
    total_weight = sum(weights.values()) or 1
    score = 100 * sum(components[k] * weights[k] for k in components) / total_weight

    flags, reasons = [], []
    if looks_keyword_stuffed(parsed):
        flags.append(f"Possible keyword stuffing ({keyword_stuffing_ratio(parsed):.0f} skill mentions "
                     f"per 100 words, each repeated {average_repetition(parsed):.1f}x)")
        score -= 15
    if must_miss:
        flags.append("Missing must-have: " + ", ".join(pretty(s) for s in must_miss))
    if min_exp and parsed.years_experience < min_exp:
        flags.append(f"Experience {parsed.years_experience:g} yrs is below the required {min_exp:g} yrs")

    reasons.append(f"Matched {len(must_hit)}/{len(must)} must-have skills")
    if nice_hit:
        reasons.append("Bonus skills: " + ", ".join(pretty(s) for s in nice_hit))
    reasons.append(f"{parsed.years_experience:g} years of experience")
    if parsed.education:
        reasons.append(f"Education: {parsed.education.title()} degree")

    score = round(max(min(score, 100), 0), 1)
    if score >= SHORTLIST_SCORE and components["must_have"] >= MIN_MUST_HAVE_FOR_SHORTLIST and not any(
            f.startswith("Possible keyword") for f in flags):
        decision = "Shortlisted"
    elif score >= REVIEW_SCORE:
        decision = "Review"
    else:
        decision = "Rejected"

    return MatchResult(similarity=round(similarity, 4), must_have_matched=must_hit, must_have_missing=must_miss,
                       nice_to_have_matched=nice_hit, components={k: round(v, 3) for k, v in components.items()},
                       score=score, decision=decision, flags=flags, reasons=reasons)
