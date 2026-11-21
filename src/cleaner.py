"""
Step 2: clean the raw text so that matching is fair and consistent.

- redact_pii(): removes emails and phone numbers. The score must depend on
  skills and experience only, never on personal details.
- clean_text(): lower-case, remove URLs and symbols, collapse whitespace.
  Characters used in skill names (+, #, /, .) are kept so that "c++",
  "ci/cd" and "node.js" survive.
"""

import re

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\d[\s-]?){9,11}\d")
URL_RE = re.compile(r"https?://\S+|www\.\S+")


def redact_pii(text: str) -> str:
    text = EMAIL_RE.sub(" ", text)
    return PHONE_RE.sub(" ", text)


def clean_text(text: str) -> str:
    text = text.lower()
    text = URL_RE.sub(" ", text)
    text = re.sub(r"[^a-z0-9+#/.\s-]", " ", text)
    text = re.sub(r"(?<![a-z0-9])[.-]|[.-](?![a-z0-9])", " ", text)  # stray dots/dashes
    return re.sub(r"\s+", " ", text).strip()
