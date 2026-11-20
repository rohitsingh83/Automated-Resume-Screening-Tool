"""End-to-end Automated Resume Screening Tool pipeline."""

import json
import logging
import sqlite3
import pandas as pd

from src.config import settings
from src.ingest import load_all_resumes
from src.extract import clean_for_nlp, parse_resume
from src.features import compute_jd_similarities
from src.rank import score_candidate
from src.visualize import save_ranking_chart

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("resume_screening")


def init_db(db_path, schema_path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    return conn


def main() -> None:
    logger.info("Starting Automated Resume Screening Pipeline...")
    jd_text = settings.jd_path.read_text(encoding="utf-8")
    cfg = json.loads(settings.skills_config_path.read_text(encoding="utf-8"))

    resumes = load_all_resumes(settings.resumes_dir)
    if not resumes:
        raise RuntimeError(f"No resumes found in {settings.resumes_dir}")

    parsed_profiles = [parse_resume(r["clean_text"], vocabulary=cfg.get("must_have", []) + cfg.get("good_to_have", [])) for r in resumes]
    jd_clean = clean_for_nlp(jd_text)
    similarities, sim_backend = compute_jd_similarities(jd_clean, [p["nlp_text"] for p in parsed_profiles])

    rows = []
    conn = init_db(settings.db_path, settings.schema_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO jobs (title, description, must_have_skills, min_years) VALUES (?, ?, ?, ?)",
            ("Python & ML Engineer", jd_text, ",".join(cfg["must_have"]), cfg.get("min_years", settings.min_years_experience)),
        )
        job_id = cur.lastrowid

        for res, prof, sim in zip(resumes, parsed_profiles, similarities):
            scored = score_candidate(
                similarity=sim,
                candidate_skills=prof["skills"],
                years_exp=prof["years_experience"],
                must_have_skills=cfg["must_have"],
                min_years=cfg.get("min_years", settings.min_years_experience),
                shortlist_threshold=settings.shortlist_threshold,
            )
            cur.execute(
                """INSERT OR REPLACE INTO candidates
                   (name, filename, raw_text, extracted_skills, years_experience, education)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (res["candidate_name"], res["filename"], res["clean_text"], ",".join(prof["skills"]), prof["years_experience"], prof["education"]),
            )
            cand_id = cur.lastrowid
            cur.execute(
                """INSERT INTO rankings
                   (job_id, candidate_id, similarity_score, must_have_ratio, final_score, status, missing_skills, explanation)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (job_id, cand_id, scored["similarity_score"], scored["must_have_ratio"], scored["final_score"], scored["status"], scored["missing_must_have"], scored["explanation"]),
            )
            rows.append({
                "candidate_name": res["candidate_name"],
                "filename": res["filename"],
                "education": prof["education"],
                "years_experience": prof["years_experience"],
                "matched_skills_count": len(prof["skills"]),
                **scored,
            })

        conn.commit()
    finally:
        conn.close()

    df = pd.DataFrame(rows).sort_values("final_score", ascending=False).reset_index(drop=True)
    df.index += 1
    df.index.name = "rank"

    out_csv = settings.outputs_dir / "screening_results.csv"
    df.to_csv(out_csv)

    shortlisted = df[df["status"] == "Shortlisted"]
    shortlisted.to_csv(settings.outputs_dir / "shortlisted_candidates.csv")

    save_ranking_chart(df, settings.images_dir / "candidate_ranking_chart.png")

    logger.info("Completed screening %d candidates (%d shortlisted). Output: %s", len(df), len(shortlisted), out_csv)
    print(f"=== Automated Resume Screening Tool ({sim_backend}) ===")
    print(df[["candidate_name", "filename", "final_score", "must_have_ratio", "status", "missing_must_have"]].to_string())
    print(f"\nSaved full report to: {out_csv}")
    print(f"Shortlisted {len(shortlisted)}/{len(df)} candidates.")


if __name__ == "__main__":
    main()
