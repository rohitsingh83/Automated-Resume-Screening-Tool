"""TF-IDF vectorization and cosine similarity computation (scikit-learn with NumPy fallback)."""

import math
from collections import Counter
from typing import List, Tuple

import numpy as np


def _pure_tfidf_cosine(jd_text: str, resume_texts: List[str]) -> List[float]:
    """Compute TF-IDF cosine similarity without external ML dependencies."""
    docs = [jd_text] + resume_texts
    tokenized = [d.lower().split() for d in docs]
    n_docs = len(docs)
    df = Counter()
    for tokens in tokenized:
        for tok in set(tokens):
            df[tok] += 1

    vocab = sorted(df.keys())
    idf = {tok: math.log((1 + n_docs) / (1 + df[tok])) + 1.0 for tok in vocab}

    vectors = []
    for tokens in tokenized:
        tf = Counter(tokens)
        vec = np.array([tf[tok] * idf[tok] for tok in vocab], dtype=float)
        norm = np.linalg.norm(vec)
        vectors.append(vec / norm if norm > 0 else vec)

    jd_vec = vectors[0]
    return [float(np.dot(jd_vec, r_vec)) for r_vec in vectors[1:]]


def compute_jd_similarities(jd_text: str, resume_texts: List[str]) -> Tuple[List[float], str]:
    """Use scikit-learn TfidfVectorizer when available, else NumPy TF-IDF."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vectorizer.fit_transform([jd_text] + resume_texts)
        sims = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
        return [float(s) for s in sims], "sklearn-tfidf"
    except ImportError:
        return _pure_tfidf_cosine(jd_text, resume_texts), "numpy-tfidf"
