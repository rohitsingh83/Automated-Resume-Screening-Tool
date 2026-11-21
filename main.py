"""
Automated Resume Screening Tool: command-line entry point.

Examples:
    python main.py                              # screen resumes/ for the Data Analyst job
    python main.py --job python_developer       # pick another job description
    python main.py --job ml_engineer --resumes path/to/folder
    python main.py --list-jobs
"""

import argparse
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.charts import ranking_chart, score_breakdown_chart, skill_gap_heatmap
from src.matcher import DEFAULT_WEIGHTS
from src.report import save_reports
from src.screener import load_jobs, screen_folder, to_dataframe

ROOT = Path(__file__).resolve().parent
STYLE = {"Shortlisted": "bold green", "Review": "yellow", "Rejected": "red"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank resumes against a job description.")
    parser.add_argument("--job", default="data_analyst", help="job id from data/job_descriptions/")
    parser.add_argument("--resumes", default=str(ROOT / "resumes"), help="folder with PDF/DOCX/TXT resumes")
    parser.add_argument("--out", default=str(ROOT / "outputs"), help="where to save the reports")
    parser.add_argument("--no-charts", action="store_true", help="skip creating PNG charts")
    parser.add_argument("--list-jobs", action="store_true", help="show available job descriptions")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    console = Console()
    jobs = load_jobs()

    if args.list_jobs:
        for job_id, job in jobs.items():
            console.print(f"[bold]{job_id}[/]  {job['title']} at {job['company']}")
        return
    if args.job not in jobs:
        console.print(f"[red]Unknown job '{args.job}'. Available: {', '.join(jobs)}[/]")
        return

    job = jobs[args.job]
    console.print(Panel.fit(
        f"[bold]{job['title']}[/] at {job['company']} ({job['location']})\n"
        f"Must-have: {', '.join(job['must_have'])}\n"
        f"Nice-to-have: {', '.join(job['nice_to_have'])}\n"
        f"Minimum experience: {job['min_experience']} years",
        title="Automated Resume Screening", border_style="blue"))

    candidates = screen_folder(job, args.resumes)
    if not candidates:
        console.print("[red]No PDF/DOCX/TXT resumes found.[/]")
        return
    df = to_dataframe(candidates)

    table = Table(title=f"Ranking of {len(df)} candidates", header_style="bold white on blue")
    for col in ["Rank", "Candidate", "File", "Score", "Decision", "Must-have %", "Experience (yrs)", "Missing must-have"]:
        table.add_column(col, justify="right" if col in {"Rank", "Score", "Must-have %", "Experience (yrs)"} else "left")
    for _, row in df.iterrows():
        table.add_row(str(row["Rank"]), row["Candidate"], row["File"], f"{row['Score']:.1f}",
                      f"[{STYLE[row['Decision']]}]{row['Decision']}[/]", f"{row['Must-have %']}%",
                      f"{row['Experience (yrs)']:g}", row["Missing must-have"])
    console.print(table)

    counts = df["Decision"].value_counts()
    console.print(f"[green]Shortlisted: {counts.get('Shortlisted', 0)}[/]  "
                  f"[yellow]Review: {counts.get('Review', 0)}[/]  [red]Rejected: {counts.get('Rejected', 0)}[/]")

    paths = save_reports(candidates, df, job, args.out)
    if not args.no_charts:
        images = ROOT / "images"
        images.mkdir(exist_ok=True)
        ranking_chart(df, job, images / f"{job['id']}_ranking.png")
        skill_gap_heatmap(candidates, job, images / f"{job['id']}_skill_gap.png")
        score_breakdown_chart(candidates, images / f"{job['id']}_score_breakdown.png", DEFAULT_WEIGHTS)

    console.print("\n[bold]Reports saved:[/]")
    for path in paths.values():
        console.print(f"  - {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}")


if __name__ == "__main__":
    main()
