# Interview Preparation: Automated Resume Screening Tool (10 Q&As)

1. **Explain your project (Non-Technical):** It's a smart screening assistant that reads candidate resumes, compares them to a job description, flags missing required skills, and ranks applicants so recruiters focus on the best matches faster.
2. **Explain your project (Technical):** It ingests `.docx`/`.pdf`/`.txt` resumes, redacts PII, extracts skills and experience via regex, computes TF-IDF cosine similarity against the JD, applies a weighted formula with must-have skill gap penalties, stores rankings in SQLite, and exposes a FastAPI endpoint.
3. **Why TF-IDF + Cosine Similarity?** TF-IDF downweights common filler words and highlights domain skills; cosine similarity normalizes for resume length.
4. **How do you handle bias and privacy?** `redact_pii()` strips emails and phone numbers before vectorization, and scoring relies strictly on skills, experience, and JD relevance.
5. **What is the purpose of the must-have skill gap penalty?** It prevents candidates with high keyword overlap from ranking high if they are missing critical core requirements.
6. **How do you parse different file formats?** `src/ingest.py` dispatches `.pdf` to `pypdf`, `.docx` to `python-docx` (including tables), and `.txt` to UTF-8 text reading.
7. **Why use SQLite in this project?** It provides zero-configuration relational persistence for jobs, candidates, and ranking audit trails.
8. **How do you evaluate the ranking quality?** `notebooks/03_eval.py` checks classification accuracy and Top-K Precision against `data/labeled_pairs.csv`.
9. **What are the limitations of regex skill matching?** Exact matching misses synonyms (e.g., "ML" vs "Machine Learning"); fuzzy matching (`rapidfuzz`) or embeddings solve this.
10. **How would you scale this to 10,000+ resumes?** Precompute `all-MiniLM-L6-v2` embeddings, index them in pgvector/FAISS, and run ingestion asynchronously via a worker queue.
