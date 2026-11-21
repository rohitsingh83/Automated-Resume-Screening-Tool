"""
Step 5: save the results.

- screening_report.csv      every candidate with score, decision and reasons
- shortlisted.csv           only the shortlisted candidates
- screening_report.xlsx     formatted Excel workbook (colour-coded decisions)
- candidate_feedback.txt    one readable paragraph per candidate for the recruiter
"""

from io import BytesIO
from pathlib import Path

import pandas as pd

from .screener import Candidate

DECISION_COLOURS = {"Shortlisted": "#C6F6D5", "Review": "#FEFCBF", "Rejected": "#FED7D7"}


def excel_bytes(df: pd.DataFrame, job: dict) -> bytes:
    """Build a formatted Excel workbook in memory (also used for the app download)."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Ranking", index=False, startrow=3)
        book, sheet = writer.book, writer.sheets["Ranking"]
        title = book.add_format({"bold": True, "font_size": 16, "font_color": "#1E3A8A"})
        sheet.write(0, 0, f"Resume Screening Report: {job['title']} ({job.get('company', '')})", title)
        sheet.write(1, 0, f"Must-have: {', '.join(job['must_have'])} | Min experience: {job.get('min_experience', 0)} yrs")
        header = book.add_format({"bold": True, "bg_color": "#1E3A8A", "font_color": "white", "border": 1})
        for col, name in enumerate(df.columns):
            sheet.write(3, col, name, header)
            width = min(max(len(str(name)), df[name].astype(str).str.len().max()) + 2, 45)
            sheet.set_column(col, col, width)
        last = len(df) + 3
        dcol = df.columns.get_loc("Decision")
        for decision, colour in DECISION_COLOURS.items():
            sheet.conditional_format(4, dcol, last, dcol, {
                "type": "cell", "criteria": "==", "value": f'"{decision}"',
                "format": book.add_format({"bg_color": colour})})
        scol = df.columns.get_loc("Score")
        sheet.conditional_format(4, scol, last, scol, {"type": "data_bar", "bar_color": "#60A5FA"})
        sheet.freeze_panes(4, 2)
    return buffer.getvalue()


def feedback_text(candidates: list[Candidate], job: dict) -> str:
    lines = [f"Candidate feedback: {job['title']}", "=" * 60, ""]
    for rank, c in enumerate(candidates, start=1):
        m = c.match
        lines.append(f"#{rank} {c.parsed.name} ({c.file}): {m.score}/100 -> {m.decision}")
        lines += [f"   + {r}" for r in m.reasons]
        lines += [f"   ! {f}" for f in m.flags]
        lines.append("")
    return "\n".join(lines)


def save_reports(candidates: list[Candidate], df: pd.DataFrame, job: dict, out_dir: str | Path) -> dict[str, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "csv": out / f"{job['id']}_screening_report.csv",
        "shortlist": out / f"{job['id']}_shortlisted.csv",
        "excel": out / f"{job['id']}_screening_report.xlsx",
        "feedback": out / f"{job['id']}_candidate_feedback.txt",
    }
    df.to_csv(paths["csv"], index=False)
    df[df["Decision"] == "Shortlisted"].to_csv(paths["shortlist"], index=False)
    paths["excel"].write_bytes(excel_bytes(df, job))
    paths["feedback"].write_text(feedback_text(candidates, job), encoding="utf-8")
    return paths
