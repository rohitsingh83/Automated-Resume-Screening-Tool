"""FastAPI service exposing resume screening endpoints."""

import json
from pathlib import Path
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

from src.extract import parse_resume
from src.features import compute_jd_similarities
from src.rank import score_candidate

app = FastAPI(title="Automated Resume Screening API", version="1.0.0")


class RankRequest(BaseModel):
    job_description: str
    must_have_skills: List[str]
    min_years: float = 1.0
    resumes: List[dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/rank")
def rank_resumes(req: RankRequest):
    parsed = [parse_resume(r["text"]) for r in req.resumes]
    sims, backend = compute_jd_similarities(req.job_description, [p["nlp_text"] for p in parsed])
    results = []
    for r, p, sim in zip(req.resumes, parsed, sims):
        scored = score_candidate(sim, p["skills"], p["years_experience"], req.must_have_skills, req.min_years)
        results.append({"name": r["name"], "skills": p["skills"], **scored})
    results.sort(key=lambda x: x["final_score"], reverse=True)
    return {"backend": backend, "ranked_candidates": results}
