# Project Explanation: Automated Resume Screening Tool

This document explains the project end to end: what it is, why each step exists, and how
the pieces fit together. Read it before an interview.

---

## 1. What is an Automated Resume Screening Tool?

**Simple explanation.** A company posts one job and receives 500 resumes. A recruiter cannot
read all of them carefully. This tool reads every resume automatically, checks it against the
job requirements, gives each candidate a score out of 100, and sorts them into
*Shortlisted*, *Review* and *Rejected*, with the reasons written next to every decision.

**Technical explanation.** It is a text-processing (NLP) pipeline. Resume files (PDF, DOCX, TXT)
are converted to text, cleaned, and parsed into structured fields (skills, years of experience,
education). The job description and every resume are converted into TF-IDF vectors and compared
with cosine similarity. That similarity is combined with rule-based checks (must-have skills,
minimum experience, degree) in a weighted, explainable formula.

### Why companies need it

| Problem without a tool | What the tool does |
|---|---|
| Recruiters spend 6–8 seconds per resume and miss good candidates | Reads every resume fully and consistently |
| Different recruiters judge differently | Same rules and weights for everyone |
| No record of *why* someone was rejected | Every decision has written reasons and flags |
| Personal details can bias decisions | Emails/phones are removed before scoring |

### How real ATS systems shortlist candidates

Applicant Tracking Systems (Workday, Greenhouse, Lever, Naukri RMS) mainly look at:

1. **Keywords and skills** from the job description (e.g. "SQL", "Power BI").
2. **Must-have gates**: a candidate missing a required skill is filtered out or pushed down.
3. **Experience**: years in relevant roles, compared with the minimum asked.
4. **Education**: degree level and field.
5. **Overall relevance**: how similar the resume text is to the job description.

This project implements all five.

### Workflow

```
resume upload → text extraction → cleaning → skill extraction → job description matching
             → score calculation → shortlist / review / reject → report generation
```

---

## 2. Tech stack options

| Option | Tools | Difficulty | Output |
|---|---|---|---|
| **A. Easy** | Python, regex keyword matching, CSV module | Beginner | Count of matching keywords per resume |
| **B. Intermediate** ✅ | Python, Pandas, pdfplumber, python-docx, regex, scikit-learn (TF-IDF + cosine similarity), Matplotlib, Streamlit | Intermediate | Weighted score, ranking, CSV/Excel reports, dashboard |
| **C. Advanced** | Option B + spaCy NER, sentence-transformers embeddings, FAISS vector search, FastAPI, PostgreSQL, Docker | Advanced | Semantic search over thousands of resumes, production API |

**Chosen: Option B, plus a FastAPI endpoint from Option C.** It uses industry-standard
libraries, every number in the score can be explained, and it runs on any laptop without a GPU.

---

## 3. Architecture

```
                   ┌─────────────────────────────┐
  INPUT            │ resumes/  (PDF, DOCX, TXT)  │   data/job_descriptions/*.json
                   └──────────────┬──────────────┘   data/skills.json (skill dictionary)
                                  │
  PROCESSING       ┌──────────────▼──────────────┐
                   │ extractor.py                │  pdfplumber / python-docx / utf-8
                   │   raw text                  │
                   ├─────────────────────────────┤
                   │ cleaner.py                  │  remove email/phone (PII), lower-case,
                   │   clean text                │  strip symbols, keep c++ / ci/cd
                   ├─────────────────────────────┤
                   │ parser.py                   │  name, skills (alias dictionary),
                   │   structured profile        │  years of experience, education
                   ├─────────────────────────────┤
                   │ matcher.py                  │  TF-IDF + cosine similarity,
                   │   score 0-100 + decision    │  must-have / nice-to-have / experience /
                   │                             │  education, keyword-stuffing check
                   ├─────────────────────────────┤
                   │ screener.py                 │  runs everything, ranks candidates
                   └──────────────┬──────────────┘
                                  │
  OUTPUT     ┌────────────────────┼─────────────────────┬──────────────────┐
             ▼                    ▼                     ▼                  ▼
      outputs/*.csv,        images/*.png           app.py              api.py
      *.xlsx, feedback.txt  (charts)               Streamlit dashboard  FastAPI REST API
```

**Data flow.** A resume file becomes raw text → clean text → a `ParsedResume` object
(skills, years, education) → a `MatchResult` (component scores, total score, decision,
reasons, flags) → one row in the ranking table → CSV/Excel/charts/dashboard.

### The scoring formula

```
score = 100 × (0.40 × must_have_coverage
             + 0.25 × content_similarity
             + 0.15 × experience_ratio
             + 0.15 × nice_to_have_coverage
             + 0.05 × education_match)
        − 15 if the resume looks keyword-stuffed
```

* `must_have_coverage` = must-have skills found / total must-have skills
* `content_similarity` = TF-IDF cosine similarity ÷ 0.45, capped at 1 (raw TF-IDF similarity
  between two different documents rarely exceeds ~0.45)
* `experience_ratio` = candidate years ÷ required years, capped at 1
* `education_match` = 1 if the degree level meets the requirement, 0.5 if lower, 0 if none found

**Decision rules**

* **Shortlisted**: score ≥ 65 **and** at least 80% of must-have skills **and** not keyword-stuffed
* **Review**: score ≥ 45 (a human should look)
* **Rejected**: everything else

---

## 4. Implementation plan (what, why, expected output, common mistakes)

| Phase | What to do | Why | Expected output | Common beginner mistakes |
|---|---|---|---|---|
| 1. Setup | Install Python 3.10+, create a virtual env, `pip install -r requirements.txt` | Isolated, reproducible environment | `pip list` shows pandas, scikit-learn… | Installing packages globally; using Python 2 |
| 2. Folders | Create `resumes/ data/ src/ outputs/ images/ docs/ tests/` | Separate data, code and results | Clean project tree | Putting everything in one file |
| 3. Sample resumes | `python scripts/create_sample_resumes.py` | No access to real applicant data; need varied test cases | 10 resumes in 3 formats | Only testing with one perfect resume |
| 4. Job description | Write JSON with must-have / nice-to-have / min experience | The screener needs clear requirements | `data/job_descriptions/*.json` | Mixing must-have and nice-to-have |
| 5. Text extraction | `src/extractor.py` | Computers can't compare files, only text | Raw text per resume | Forgetting DOCX tables; scanned PDFs have no text |
| 6. Cleaning | `src/cleaner.py` | Fair matching, no PII bias | Lower-case clean text | Removing `+` and `/`, which breaks "C++" and "CI/CD" |
| 7. Skill matching | `src/parser.py` + `data/skills.json` | "sklearn" and "scikit-learn" are the same skill | Set of canonical skills | Substring matching ("ml" inside "html") |
| 8. Scoring | `src/matcher.py` | Turn evidence into one comparable number | Score 0–100 with reasons | Black-box score with no explanation |
| 9. Ranking & shortlist | `src/screener.py` | Recruiters need an ordered list | Ranked DataFrame | Shortlisting on score alone, ignoring must-haves |
| 10. Reports | `src/report.py`, `src/charts.py` | Results must be shareable | CSV, Excel, PNG charts | Saving reports with absolute paths |
| 11. GitHub | Commit, push, add screenshots | Proof of work | Public repository | Committing `venv/` or secrets |

---

## 8. Virtual simulation: how a real HR screening run is simulated

1. **Sample resumes**: `scripts/create_sample_resumes.py` creates 10 fictional candidates with
   realistic variety: strong matches, a fresher, a career changer, a frontend developer applying
   for the wrong role, and one keyword-stuffed resume that tries to trick the system.
2. **Job descriptions**: three realistic roles in `data/job_descriptions/` (Data Analyst,
   Python Backend Developer, ML Engineer), each with must-have and nice-to-have skills.
3. **Required skills**: `data/skills.json` lists ~45 skills with their aliases, grouped
   by category.
4. **Text extraction**: `pdfplumber` for PDFs, `python-docx` for Word, plain read for TXT.
5. **Matching score**: TF-IDF similarity plus rule checks (see formula above).
6. **Ranking**: candidates are sorted by score; ties keep the original order.
7. **Shortlist decision**: the decision rules above, with reasons and warning flags.

The same resumes give *different* rankings for different jobs: Kabir ranks #1 for the Python
developer role but is rejected for the Data Analyst role. That shows the tool is matching
against the job, not just counting skills.

### Outputs to save and upload to GitHub

* `outputs/<job>_screening_report.csv`: full ranking
* `outputs/<job>_shortlisted.csv`: shortlisted only
* `outputs/<job>_screening_report.xlsx`: formatted Excel
* `outputs/<job>_candidate_feedback.txt`: reasons for every candidate
* `images/*.png`: ranking chart, skill-gap heatmap, score breakdown, dashboard screenshots

---

## 12. Proof-building plan (day by day)

| Day | Work | Commit message example | Screenshot to save |
|---|---|---|---|
| 1 | Setup, folders, sample data, job descriptions | `chore: project setup with sample resumes and job descriptions` | Project folder in VS Code |
| 2 | Text extraction + cleaning + parsing | `feat: extract and parse text from PDF, DOCX and TXT resumes` | Terminal showing parsed skills |
| 3 | TF-IDF matching and scoring | `feat: TF-IDF similarity and weighted candidate scoring` | Score output |
| 4 | Ranking, shortlist rules, CLI | `feat: ranking, shortlist decisions and reports` | Ranking table in terminal |
| 5 | Reports, charts, dashboard | `feat: Streamlit recruiter dashboard` | Dashboard tabs, CSV in Excel |
| 6 | Tests, README, screenshots | `docs: README, interview prep and screenshots` | GitHub repo page |

## 13. Screenshots checklist

- [ ] Project folder structure (VS Code explorer)
- [ ] `resumes/` folder showing PDF, DOCX and TXT files
- [ ] Terminal output of `python main.py`
- [ ] Ranking table (terminal or dashboard)
- [ ] Shortlisted candidates CSV opened in Excel
- [ ] Dashboard: Overview, Candidate profile, Skill gaps tabs
- [ ] `pytest` passing
- [ ] GitHub repository page
