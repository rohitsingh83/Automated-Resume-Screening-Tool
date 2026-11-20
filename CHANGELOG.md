# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-20

### Added
- Standard `pyproject.toml` with PEP 621 packaging metadata and bounded dependencies.
- Centralized `Settings` configuration dataclass in `src/config.py` with environment variable overrides.
- Model Card documentation (`MODEL_CARD.md`) detailing algorithmic architecture, intended use, and bias protections.
- Performance profiling and complexity documentation (`PERF.md`).
- Formal Architecture Decisions Record (`DECISIONS.md`).
- GitHub Actions CI matrix workflow (`.github/workflows/ci.yml`).
- Expanded test suite covering edge cases and zero-skill resume profiles.

### Changed
- Refactored `main.py` to use `src.config.settings` and standard structured logging.
- Wrapped database connection lifecycles in `try...finally` resource managers.
- Upgraded Streamlit dashboard with candidate score cards and status filtering.

### Fixed
- Fixed naive tenure extraction to filter out spurious telephone/postal number artifacts.
