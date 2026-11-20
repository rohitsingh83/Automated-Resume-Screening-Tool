# Engineering Audit: Automated Resume Screening Tool

**Project Context:**
- **What it does / who it's for:** An automated ATS candidate screening pipeline that extracts text from resumes (`.pdf`, `.docx`, `.txt`), redacts PII, extracts skills/experience, computes TF-IDF semantic match scores against a job description, applies gap penalties, and produces ranked candidate shortlists.
- **Stack & entry points:** Python 3.14 / 3.11, `scikit-learn`, `pypdf`, `python-docx`, `pandas`, `sqlite3`, `fastapi`, `streamlit`. Entry points: `python main.py`, `python notebooks/03_eval.py`, `python -m uvicorn api.app:app`, `python -m streamlit run app_streamlit.py`.
- **Real usage:** Hybrid batch processing script (`main.py`) + REST microservice (`api/app.py`) + interactive evaluation UI (`app_streamlit.py`).
- **Constraint:** Preserve `main.py` entry point, database schema in `db/schema.sql`, output CSV schemas in `outputs/`, and FastAPI `/rank` request/response shape.

---

## Findings & Technical Debt

### 🔴 Critical Findings
1. **Unstable TF-IDF Vectorizer Fitting on Tiny Dynamic Corpus (`src/features.py`):**
   - In `compute_jd_similarities()`, `TfidfVectorizer` is fit on `[jd_text] + resume_texts` dynamically on every single call. When screening 3–6 resumes, IDF values become statistically degenerate. A single resume mentioning a common word that happens not to be in the other 2 resumes gets an artificially massive IDF weight.
2. **Naive Single-Instance Experience Extraction (`src/extract.py`):**
   - `extract_years_experience()` uses `re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)")` and computes `max()`. A candidate with 3 distinct jobs of "2 years", "3 years", and "1 year" is assigned `3.0` years instead of total career tenure `6.0` years. Furthermore, strings like "30 years old" or phone numbers before "years" can trigger catastrophic false positives.
3. **Database Connection Resource Leak on Failure (`main.py`):**
   - `conn = init_db(...)` is initialized without a context manager (`with sqlite3.connect...`). If parsing or vectorization raises an unhandled exception, the database connection is never committed or closed properly, leading to locked SQLite database files on Windows.

### 🟡 High Priority Findings
4. **Hardcoded Module-Level Skills Dictionary vs Decoupled Config (`src/extract.py` vs `data/skills_config.json`):**
   - `src/extract.py` defines a static hardcoded `SKILLS_DICTIONARY` list of 28 items, whereas `data/skills_config.json` defines job-specific `must_have` and `good_to_have` skills. The extractor defaults to the hardcoded list unless manually overridden, creating divergence between extraction vocabulary and scoring requirements.
5. **Magic Numbers in Scoring Formulation (`src/rank.py`):**
   - Weights `0.45`, `0.45`, `0.10`, penalty factor `0.05`, and threshold `0.55` are hardcoded directly in the equation without configuration abstraction.
6. **No Packaging or Centralized Settings (`pyproject.toml`):**
   - Relies on script execution with `sys.path` side-effects. No PEP 621 `pyproject.toml`, no Pydantic settings schema for threshold and path validation.
7. **Unbounded Input Vulnerability in API (`api/app.py`):**
   - `/rank` endpoint does not validate minimum or maximum resume string lengths, nor does it sanitize inputs, allowing Denial-of-Service via megabyte-long text payloads or empty strings.

### 🟢 Nice-to-Have / Polish
8. **Missing Fast/Slow Test Categorization:**
   - Unit tests run the full scikit-learn TF-IDF pipeline and docx parsers together; needs separation between fast unit tests and integration tests.
9. **Lack of Run Manifest and Reproducibility Metadata:**
   - Model outputs overwrite `screening_results.csv` in place without logging config hash, run timestamp, data fingerprint, or environment locks.

---

## What "Elite" Looks Like for This Exact Project

An elite ATS screening engine:
- Uses a unified, validated `Settings` configuration loaded from environment/YAML.
- Computes TF-IDF with pre-trained/smoothed IDF weights or standard n-gram tokenization with stop-word curation.
- Extracts experience by parsing work experience date intervals (e.g. `2020 - 2023`) or structured duration summation with regex fallback.
- Packages code under standard `src/` layout with `pyproject.toml`, strict MyPy type checking, and Ruff formatting.
- Features idempotent SQLite persistence wrapped in transaction context managers.
- Produces a timestamped `run_manifest.json` detailing data hash, vectorizer config, candidate count, and score distributions.
