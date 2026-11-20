# Architecture & Engineering Decisions (ADR)

## ADR 001: Configuration Management & Schema Validation
- **Status:** Accepted
- **Context:** Hardcoded paths (`data/job_description.txt`, `data/skills_config.json`, `db/screening.db`) and scoring thresholds (`0.55`, `0.60`) were scattered across `main.py` and `src/rank.py`.
- **Decision:** Introduce a single immutable dataclass-backed `Settings` class in `src/config.py` with environment variable overrides, input validation, and absolute path resolution anchored to project root.
- **Consequences:** Eliminates hardcoded magic constants, makes tests independent of invocation working directory, and allows environment-specific configurations.

## ADR 002: TF-IDF Vectorization & Feature Engineering
- **Status:** Accepted
- **Context:** Fitting a dynamic TF-IDF vectorizer on tiny batches ($\le 6$ documents) yields statistically noisy inverse document frequencies.
- **Decision:** Retain scikit-learn's `TfidfVectorizer` with `sublinear_tf=True`, `ngram_range=(1, 2)`, and smooth IDF enabled. Provide fallback pure NumPy vectorizer for zero-dependency environments.
- **Consequences:** Preserves zero-external-service execution while stabilizing scores across varying candidate batch sizes.

## ADR 003: Experience Extraction Aggregation
- **Status:** Accepted
- **Context:** Using `max()` on regex-extracted years resulted in under-counting candidates with multiple distinct tenure periods.
- **Decision:** Add tenure accumulation for distinct position matches while maintaining a sensible cap (max 40 years) to filter phone number / pincode noise.
- **Consequences:** Fairer candidate evaluation without breaking existing test assertions.
