"""Candidate scoring, gap-penalty calculation, ranking, and explanation builder."""

from typing import Dict, List


def score_candidate(
    similarity: float,
    candidate_skills: List[str],
    years_exp: float,
    must_have_skills: List[str],
    min_years: float = 1.0,
    shortlist_threshold: float = 0.55,
) -> Dict:
    """Compute weighted ATS score, must-have skill gaps, and shortlist status."""
    must_set = [s.lower() for s in must_have_skills]
    cand_set = set(s.lower() for s in candidate_skills)

    matched_must = [s for s in must_set if s in cand_set]
    missing_must = [s for s in must_set if s not in cand_set]

    must_total = max(1, len(must_set))
    must_ratio = len(matched_must) / must_total
    exp_ratio = min(1.0, years_exp / max(0.5, min_years))
    gap_penalty = 0.05 * len(missing_must)

    raw_score = 0.45 * similarity + 0.45 * must_ratio + 0.10 * exp_ratio - gap_penalty
    final_score = round(max(0.0, min(1.0, raw_score)), 4)

    status = "Shortlisted" if (final_score >= shortlist_threshold and must_ratio >= 0.6) else "Rejected"

    warning = (
        f"Missing {len(missing_must)} must-have skill(s): {', '.join(missing_must)}"
        if missing_must
        else "All must-have skills matched"
    )

    return {
        "similarity_score": round(similarity, 4),
        "must_have_ratio": round(must_ratio, 4),
        "final_score": final_score,
        "status": status,
        "matched_must_have": ", ".join(matched_must) if matched_must else "None",
        "missing_must_have": ", ".join(missing_must) if missing_must else "None",
        "explanation": warning,
    }
