# Automated Resume Screening Tool

A modern NLP and ATS (Applicant Tracking System) screening engine built with Python, scikit-learn, SQLite, and FastAPI. It analyzes candidates across `.docx`, `.pdf`, and `.txt` formats, removes PII to protect privacy, computes TF-IDF semantic relevance against target job descriptions, flags must-have skill deficiencies, and outputs ranked recommendations.

---

## 🏛 Architecture & Processing Pipeline

```
[Resume Files: PDF / DOCX / TXT]
               │
               ▼
   [Text Extraction & Normalization]
               │
               ▼
    [Automated PII Redaction]  (Protects Emails / Phone Numbers)
               │
               ▼
[Skill & Experience Regex Parser]  (Must-have & Good-to-have matching)
               │
               ▼
   [TF-IDF & Cosine Similarity]   (Job Description vs Candidate)
               │
               ▼
    [Multi-Factor ATS Scorer]     (Similarity + Skills + Experience - Penalties)
               │
               ▼
 [SQLite Storage & CSV Reports] + [Interactive Streamlit & FastAPI]
```

---

## ✨ Key Capabilities

- **Multi-Extension Ingestion:** Extracts text cleanly from `.pdf` (via `pypdf`), `.docx` (via `python-docx`), and plain `.txt`.
- **Privacy-Preserving NLP:** Redacts sensitive PII (emails, phone numbers) before passing text to vectorization.
- **Explainable Scoring Engine:** Combines semantic relevance (45%), must-have requirements matching (45%), and experience weighting (10%), offset by missing-skill penalties.
- **Relational Audit Trail:** Records all jobs, candidate profiles, similarity scores, and final decisions into SQLite (`db/screening.db`).
- **RESTful API Service:** Provides `/health` and `/rank` endpoints via FastAPI for microservice integration.
- **Interactive Web Interface:** Streamlit dashboard with real-time candidate score breakdown, status filters, and visual analytics.

---

## 📐 Scoring Formula

The candidate match score is calculated as:

$$\text{Raw Score} = 0.45 \cdot \text{Sim} + 0.45 \cdot \text{MustRatio} + 0.10 \cdot \text{ExpRatio} - 0.05 \cdot N_{\text{missing}}$$

- **Sim:** TF-IDF Cosine similarity between resume and job description.
- **MustRatio:** Proportion of must-have skills satisfied.
- **ExpRatio:** Ratio of candidate experience relative to minimum job requirement.
- **$N_{\text{missing}}$:** Count of critical must-have skills absent.
- **Shortlist Condition:** Candidate score $\ge 0.55$ and $\text{MustRatio} \ge 0.60$.

---

## 🚀 Quick Start Guide

### 1. Environment Setup
```bash
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Run Pipeline
```bash
python main.py
```

### 3. Launch Web Dashboard
```bash
python -m streamlit run app_streamlit.py
```

### 4. Start REST API
```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Execute Test Suite
```bash
python -m unittest discover -s tests -v
```

---

## 🔌 API Documentation

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Healthcheck and readiness probe. |
| `POST` | `/rank` | Accepts job description, must-have skills, and candidate texts; returns ranked profiles. |

---

## 📊 Sample Visualizations

The pipeline automatically outputs ranking comparison charts into `images/candidate_ranking_chart.png`.
