import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from src.extract import (
    extract_skills,
    redact_pii,
    extract_years_experience,
    extract_education,
    clean_for_nlp,
    parse_resume,
)
from src.features import compute_jd_similarities, _pure_tfidf_cosine
from src.rank import score_candidate
from api.app import app


class TestResumeScreening(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_pii_redaction(self):
        """Verify emails and phone numbers are safely redacted."""
        cleaned = redact_pii("Contact me at test.user@example.com or +91 9876543210")
        self.assertNotIn("test.user@example.com", cleaned)
        self.assertIn("[EMAIL]", cleaned)
        self.assertNotIn("9876543210", cleaned)
        self.assertIn("[PHONE]", cleaned)

    def test_clean_for_nlp(self):
        """Verify clean_for_nlp lowercases, redacts, and strips symbols."""
        cleaned = clean_for_nlp("Senior Software Dev: test@domain.com, 5+ yrs in Python & SQL!")
        self.assertIn("email", cleaned)
        self.assertIn("python", cleaned)
        self.assertIn("sql", cleaned)

    def test_skill_extraction(self):
        """Verify keyword skill extraction with word boundary checks."""
        skills = extract_skills("Built ML pipelines in Python using Pandas, NumPy, SQL and Git.")
        for expected in ["python", "pandas", "numpy", "sql", "git"]:
            self.assertIn(expected, skills)

    def test_extract_years_experience(self):
        """Verify numerical parsing of experience from resume texts."""
        self.assertEqual(extract_years_experience("Has 4.5 years of industry experience."), 4.5)
        self.assertEqual(extract_years_experience("Completed 6 months internship."), 0.5)
        self.assertEqual(extract_years_experience("Fresh graduate with strong academic background."), 0.0)

    def test_extract_education(self):
        """Verify degree qualification extraction."""
        self.assertEqual(extract_education("Completed B.Tech in Computer Science."), "B.TECH")
        self.assertEqual(extract_education("Holds an MCA degree from Delhi University."), "MCA")
        self.assertEqual(extract_education("Self-taught developer with portfolio."), "Not Specified")

    def test_parse_resume(self):
        """Verify end-to-end resume text parsing into structured profile."""
        raw = "John Doe | john@example.com | 3 yrs experience | B.Tech | Skills: Python, SQL, Docker"
        profile = parse_resume(raw)
        self.assertIn("python", profile["skills"])
        self.assertIn("sql", profile["skills"])
        self.assertIn("docker", profile["skills"])
        self.assertEqual(profile["years_experience"], 3.0)
        self.assertEqual(profile["education"], "B.TECH")
        self.assertIn("email", profile["nlp_text"])

    def test_tfidf_cosine(self):
        """Verify TF-IDF cosine similarity discriminates between relevant and irrelevant profiles."""
        jd = "python machine learning engineer pandas scikit-learn"
        r1 = "experienced python engineer specialized in pandas scikit-learn machine learning"
        r2 = "graphic designer with experience in photoshop and illustrator"
        sims, backend = compute_jd_similarities(jd, [r1, r2])
        self.assertGreater(sims[0], sims[1])
        self.assertGreater(sims[0], 0.5)

        # Pure numpy fallback verification
        pure_sims = _pure_tfidf_cosine(jd, [r1, r2])
        self.assertGreater(pure_sims[0], pure_sims[1])

    def test_shortlist_and_gap_warning(self):
        """Verify high scoring candidates with missing skills get correct flags."""
        res = score_candidate(0.8, ["python", "pandas", "numpy", "sql", "git"], 2.0, ["python", "pandas", "numpy", "scikit-learn", "sql", "git"])
        self.assertEqual(res["status"], "Shortlisted")
        self.assertIn("scikit-learn", res["missing_must_have"])

    def test_rejection_low_skills_and_similarity(self):
        """Verify unqualified candidates are rejected."""
        res = score_candidate(
            similarity=0.2,
            candidate_skills=["html", "css"],
            years_exp=0.0,
            must_have_skills=["python", "pandas", "numpy", "scikit-learn"],
            min_years=2.0,
            shortlist_threshold=0.55,
        )
        self.assertEqual(res["status"], "Rejected")
        self.assertEqual(res["must_have_ratio"], 0.0)
        self.assertIn("Missing 4 must-have skill(s)", res["explanation"])

    def test_perfect_candidate_score(self):
        """Verify a candidate with 100% skill match and high similarity receives top marks."""
        skills = ["python", "sql", "fastapi"]
        res = score_candidate(
            similarity=0.95,
            candidate_skills=skills,
            years_exp=4.0,
            must_have_skills=skills,
            min_years=2.0,
        )
        self.assertEqual(res["status"], "Shortlisted")
        self.assertEqual(res["must_have_ratio"], 1.0)
        self.assertEqual(res["missing_must_have"], "None")
        self.assertGreaterEqual(res["final_score"], 0.85)

    def test_empty_resume_handling(self):
        """Verify graceful parsing and scoring of empty or minimal text."""
        profile = parse_resume("")
        self.assertEqual(profile["skills"], [])
        self.assertEqual(profile["years_experience"], 0.0)
        self.assertEqual(profile["education"], "Not Specified")

    def test_api_health(self):
        """Verify health check endpoint returns 200 OK."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"status": "ok"})

    def test_api_rank_endpoint(self):
        """Verify the rank API endpoint produces sorted candidates."""
        payload = {
            "job_description": "Looking for Python backend developer with FastAPI and SQL expertise.",
            "must_have_skills": ["python", "fastapi", "sql"],
            "min_years": 1.0,
            "resumes": [
                {"name": "Alice", "text": "Python backend developer with 3 years experience building APIs with FastAPI and SQL."},
                {"name": "Bob", "text": "Junior developer familiar with HTML and CSS."},
            ],
        }
        resp = self.client.post("/rank", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("ranked_candidates", data)
        self.assertEqual(len(data["ranked_candidates"]), 2)
        self.assertEqual(data["ranked_candidates"][0]["name"], "Alice")
        self.assertEqual(data["ranked_candidates"][0]["status"], "Shortlisted")


if __name__ == "__main__":
    unittest.main()
