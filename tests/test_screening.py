"""Run with:  python -m pytest -q"""

from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from api import app
from src.cleaner import clean_text, redact_pii
from src.extractor import extract_text, list_resumes
from src.matcher import score_candidate
from src.parser import extract_education, extract_experience_years, parse_resume
from src.screener import load_jobs, screen_folder, screen_texts, to_dataframe

ROOT = Path(__file__).resolve().parent.parent
TODAY = date(2026, 11, 21)


def test_all_formats_extract_text():
    files = list_resumes(ROOT / "resumes")
    assert {f.suffix for f in files} == {".pdf", ".docx", ".txt"}
    for f in files:
        assert len(extract_text(f)) > 200, f.name


def test_pii_is_redacted_and_text_cleaned():
    text = redact_pii("Call +91 98450 11223 or mail a.b@example.com")
    assert "98450" not in text and "@" not in text
    assert clean_text("Skills: C++, CI/CD & Node.js!") == "skills c++ ci/cd node.js"


def test_skill_aliases_are_normalised():
    parsed = parse_resume("Jane Doe\nSkills: sklearn, PowerBI, k8s, Postgres")
    assert {"scikit-learn", "power bi", "kubernetes", "sql"} <= set(parsed.skills)


def test_short_aliases_do_not_match_inside_words():
    parsed = parse_resume("John Roe\nI enjoy html and xml documents")
    assert "machine learning" not in parsed.skills  # "ml" inside "html"/"xml" must not count


def test_experience_merges_overlapping_periods():
    text = "Analyst (Jan 2020 - Dec 2021)\nFreelancer (Jun 2021 - Dec 2022)"
    assert extract_experience_years(text, TODAY) == 3.0


def test_education_levels():
    assert extract_education("M.Tech in AI, 2020") == "master"
    assert extract_education("B.E. in Information Technology") == "bachelor"
    assert extract_education("Diploma in Computer Applications") == "diploma"


def test_strong_candidate_beats_weak_candidate():
    job = load_jobs()["data_analyst"]
    resumes = [
        ("strong.txt", "Asha Rao\nData analyst. Python, SQL, Excel, Pandas, data visualization, Power BI.\n"
                       "Experience\nAnalyst, Acme (Jan 2021 - Present)\nEducation\nB.Tech in CS"),
        ("weak.txt", "Ravi Kumar\nChef with 5 years of experience in Italian cuisine.\nEducation\nB.Com"),
    ]
    ranked = screen_texts(job, resumes, today=TODAY)
    assert ranked[0].file == "strong.txt"
    assert ranked[0].match.decision == "Shortlisted"
    assert ranked[1].match.decision == "Rejected"


def test_keyword_stuffing_is_flagged():
    job = load_jobs()["data_analyst"]
    ranked = {c.file: c for c in screen_folder(job, ROOT / "resumes", today=TODAY)}
    stuffed = ranked["vikram_joshi.txt"].match
    assert any("keyword stuffing" in f for f in stuffed.flags)
    assert stuffed.decision != "Shortlisted"


def test_missing_must_have_is_reported():
    job = {"must_have": ["python", "django"], "nice_to_have": [], "min_experience": 0, "education": None}
    result = score_candidate(parse_resume("A B\nPython developer"), 0.2, job)
    assert result.must_have_missing == ["django"]
    assert any("django" in f.lower() for f in result.flags)


def test_dataframe_is_ranked():
    df = to_dataframe(screen_folder(load_jobs()["python_developer"], ROOT / "resumes", today=TODAY))
    assert list(df["Rank"]) == list(range(1, len(df) + 1))
    assert df["Score"].is_monotonic_decreasing


def test_api_screen_endpoint():
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    files = [("files", (p.name, p.read_bytes())) for p in list_resumes(ROOT / "resumes")[:3]]
    resp = client.post("/screen/data_analyst", files=files)
    assert resp.status_code == 200
    assert resp.json()["count"] == 3
    assert client.post("/screen/unknown", files=files).status_code == 404
