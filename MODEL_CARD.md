# Model Card: TF-IDF ATS Resume Matcher

## Model Details
- **Architecture:** TF-IDF (Term Frequency - Inverse Document Frequency) with Cosine Similarity.
- **N-gram Range:** (1, 2) word n-grams.
- **Normalization:** L2 Euclidean norm.
- **Sublinear TF Scaling:** Enabled ($1 + \log(TF)$).
- **Domain:** Human Resources / ATS Technical Candidate Screening.

## Intended Use
- Automated pre-screening assistance to prioritize candidate resumes against structured job descriptions.
- Transparent, explainable scoring highlighting matched vs missing required skills.

## Out-of-Scope Use Cases
- Sole decision-maker for automated employment rejection without human recruiter review.
- Processing non-English resumes without domain vocabulary translation.

## Fairness & Privacy Safeguards
- **PII Redaction:** Automated regex masking of email addresses and telephone numbers before vectorization.
- **Skill-First Weighting:** Scoring formula allocates 90% of weight to semantic relevance and skill overlap, with 10% experience tenure weighting.
