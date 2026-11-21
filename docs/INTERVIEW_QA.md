# Interview Preparation: Automated Resume Screening Tool

Each answer has a short **HR version** (for non-technical interviewers) and a
**technical version** (for engineers). Practise saying them out loud.

---

### 1. Explain your project.

**HR version:** I built a tool that reads resumes automatically and compares them with a job
description. It gives each candidate a score out of 100, sorts them into shortlisted, review
and rejected, and explains every decision, for example "matched 5 of 5 must-have skills" or
"missing SQL". Recruiters get a ranked list and a dashboard instead of reading hundreds of
resumes by hand.

**Technical version:** It's a Python NLP pipeline. I extract text from PDF, DOCX and TXT using
pdfplumber and python-docx, remove personal data with regex, and parse skills using a
dictionary of about 45 skills with aliases. I compute TF-IDF vectors for the job description
and every resume and measure cosine similarity. The final score is a weighted formula: 40%
must-have skills, 25% text similarity, 15% experience, 15% nice-to-have skills and 5%
education, with a penalty for keyword stuffing. Results go to CSV and Excel reports, a
Streamlit dashboard and a FastAPI endpoint. It has 11 pytest tests.

### 2. What problem does it solve?

Manual screening is slow, inconsistent and hard to audit. A recruiter spends a few seconds per
resume and two recruiters may judge the same resume differently. The tool applies the same
rules to everyone, works in seconds, and records the reason for each decision.

### 3. Why did you choose TF-IDF and cosine similarity?

TF-IDF (Term Frequency × Inverse Document Frequency) gives high weight to words that are
frequent in one document but rare across all documents, such as "tableau" or "django", and low
weight to common words like "work" or "team". Cosine similarity compares the *direction* of
two vectors, not their length, so a long resume doesn't win just because it has more words.
Both are fast, need no training data, and are easy to explain.

### 4. Why not use only TF-IDF similarity for the score?

Similarity alone can be fooled. A resume can be similar to the job description and still miss
a critical skill. That's why must-have skills carry 40% of the score, and a candidate needs
at least 80% of them to be shortlisted. Combining semantic similarity with explicit rules is
how most real ATS systems work.

### 5. How do you extract skills accurately?

I keep a skill dictionary (`data/skills.json`) where each skill has aliases: "sklearn" and
"scikit learn" both map to "scikit-learn", and "PowerBI" maps to "power bi". Matching uses regex
with custom word boundaries, so "ml" doesn't match inside "html", and skills with symbols like
"C++" or "CI/CD" still work.

### 6. How do you calculate years of experience?

I find the experience section, then extract date ranges like "Jun 2022 – Present" or
"2019 – 2021" with regex. I convert them to month numbers, **merge overlapping periods** so two
parallel jobs aren't double-counted, and sum the months. If there are no dates, I fall back to
phrases like "3+ years of experience".

### 7. How do you handle keyword stuffing?

Some candidates paste "Python Python SQL SQL" to fool ATS systems. I measure two signals:
skill mentions per 100 words and how many times each skill is repeated on average. Genuine
resumes in my tests stay below 30 mentions per 100 words and 2.7 repetitions. If both thresholds
are crossed, the resume is flagged, loses 15 points, and can't be auto-shortlisted.

### 8. How did you make the tool fair?

Emails and phone numbers are removed before the text is vectorised, and the score only uses
skills, experience, education and job relevance. Name, gender, age, photo or location are never
used. Every decision is explainable, so a recruiter can check it. The "Review" category means
borderline cases still go to a human.

### 9. What outputs does the project generate?

A ranked CSV, a shortlist CSV, a colour-coded Excel report, a text file of feedback per
candidate, three PNG charts (ranking, skill-gap heatmap, score breakdown), an interactive
dashboard, and JSON results from the API.

### 10. What challenges did you face?

* **Different file formats:** DOCX resumes often keep skills in tables, so I read tables as well.
* **Skill variations:** solved with the alias dictionary.
* **Over-counting experience:** solved by merging overlapping date ranges and only reading the
  experience section (otherwise education years were counted as work).
* **Calibrating the score:** TF-IDF similarity values are naturally small, so I rescaled them
  and tuned the keyword-stuffing thresholds by looking at real numbers from the sample resumes.

### 11. How did you test it?

With pytest: extraction for all three formats, PII removal, alias normalisation, the "ml in
html" edge case, overlapping experience, education detection, a strong-vs-weak ranking test,
keyword-stuffing detection and the API endpoint. Run `python -m pytest -q`.

### 12. How would you scale it to 10,000 resumes?

Extract text once and store it in a database, compute vectors in batches, and use sentence
embeddings with a vector index (FAISS or pgvector) for fast semantic search. The FastAPI
service could run behind a queue so uploads are processed in the background.

### 13. How can the project be improved?

Sentence-transformer embeddings for meaning ("built dashboards" ≈ "data visualization"),
spaCy NER for company and job-title extraction, OCR for scanned PDFs, learning weights from
recruiter decisions, and integration with job portals.

### 14. What is the difference between must-have and nice-to-have skills?

Must-have skills are requirements: without them the person can't do the job, so they carry 40%
of the score and gate the shortlist. Nice-to-have skills are bonuses that separate good
candidates from great ones (15%).

### 15. How would you explain this to a non-technical person?

"It's like a very fast, very consistent assistant that reads every resume, ticks off the
skills the job needs, and hands the recruiter a sorted list with notes on each person."
