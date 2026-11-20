"""Centralized configuration and settings validation for Resume Screening Tool."""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class Settings:
    root_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(init=False)
    db_dir: Path = field(init=False)
    outputs_dir: Path = field(init=False)
    images_dir: Path = field(init=False)
    resumes_dir: Path = field(init=False)
    
    db_path: Path = field(init=False)
    schema_path: Path = field(init=False)
    jd_path: Path = field(init=False)
    skills_config_path: Path = field(init=False)
    
    shortlist_threshold: float = float(os.getenv("SHORTLIST_THRESHOLD", "0.55"))
    min_must_have_ratio: float = float(os.getenv("MIN_MUST_HAVE_RATIO", "0.60"))
    min_years_experience: float = float(os.getenv("MIN_YEARS_EXPERIENCE", "1.0"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def __post_init__(self):
        root = self.root_dir
        object.__setattr__(self, "data_dir", root / "data")
        object.__setattr__(self, "db_dir", root / "db")
        object.__setattr__(self, "outputs_dir", root / "outputs")
        object.__setattr__(self, "images_dir", root / "images")
        object.__setattr__(self, "resumes_dir", root / "resumes")
        
        object.__setattr__(self, "db_path", root / "db" / "screening.db")
        object.__setattr__(self, "schema_path", root / "db" / "schema.sql")
        object.__setattr__(self, "jd_path", root / "data" / "job_description.txt")
        object.__setattr__(self, "skills_config_path", root / "data" / "skills_config.json")
        
        # Ensure runtime directories exist
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
