"""Generate portfolio-ready screening charts."""

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def save_ranking_chart(df: pd.DataFrame, output_path: Path) -> None:
    """Save horizontal bar chart of candidate scores colored by shortlist status."""
    ordered = df.sort_values("final_score", ascending=True)
    colors = ["#2E7D32" if s == "Shortlisted" else "#C62828" for s in ordered["status"]]

    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(ordered["candidate_name"], ordered["final_score"], color=colors, height=0.55)
    ax.axvline(0.55, color="#1565C0", linestyle="--", linewidth=1.2, label="Shortlist Threshold (0.55)")
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Final ATS Match Score (0 - 1)")
    ax.set_title("Automated Resume Screening - Candidate Ranking", fontweight="bold")
    ax.legend(loc="lower right")

    for bar, score in zip(bars, ordered["final_score"]):
        ax.text(score + 0.015, bar.get_y() + bar.get_height() / 2, f"{score:.2f}", va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
