"""Charts for the README and reports (Matplotlib, saved as PNG)."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .parser import pretty
from .screener import Candidate

COLOURS = {"Shortlisted": "#16A34A", "Review": "#F59E0B", "Rejected": "#DC2626"}
def ranking_chart(df: pd.DataFrame, job: dict, path: Path) -> None:
    data = df.sort_values("Score")
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(data["Candidate"], data["Score"], color=[COLOURS[d] for d in data["Decision"]])
    ax.axvline(65, color="#16A34A", ls="--", lw=1)
    ax.axvline(45, color="#F59E0B", ls="--", lw=1)
    for bar, score in zip(bars, data["Score"]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2, f"{score:.0f}", va="center", fontsize=9)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in COLOURS.values()]
    ax.legend(handles, COLOURS.keys(), loc="lower right")
    ax.set_xlim(0, 105)
    ax.set_xlabel("Match score (0-100)")
    ax.set_title(f"Candidate ranking: {job['title']}", fontsize=14, weight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def skill_gap_heatmap(candidates: list[Candidate], job: dict, path: Path) -> None:
    skills = job["must_have"] + job["nice_to_have"]
    names = [c.parsed.name for c in candidates]
    grid = np.array([[1 if s in c.parsed.skills else 0 for s in skills] for c in candidates])
    fig, ax = plt.subplots(figsize=(11, 6))
    cmap = matplotlib.colors.ListedColormap(["#FECACA", "#BBF7D0"])
    ax.imshow(grid, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(skills)), [pretty(s) for s in skills], rotation=35, ha="right")
    ax.set_yticks(range(len(names)), names)
    ax.axvline(len(job["must_have"]) - 0.5, color="black", lw=2)
    ax.set_title("Skill coverage (left of the line = must-have, right = nice-to-have)", fontsize=12, weight="bold")
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            ax.text(j, i, "✓" if grid[i, j] else "✗", ha="center", va="center", fontsize=12,
                    color="#166534" if grid[i, j] else "#991B1B", weight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def score_breakdown_chart(candidates: list[Candidate], path: Path, weights: dict) -> None:
    names = [c.parsed.name for c in candidates][::-1]
    parts = list(weights)
    palette = ["#1E3A8A", "#2563EB", "#60A5FA", "#93C5FD", "#BFDBFE"]
    fig, ax = plt.subplots(figsize=(10, 6))
    left = np.zeros(len(names))
    for part, colour in zip(parts, palette):
        values = np.array([100 * c.match.components[part] * weights[part] for c in candidates][::-1])
        ax.barh(names, values, left=left, color=colour, label=part.replace("_", " ").title())
        left += values
    ax.set_xlabel("Points contributed to the final score")
    ax.set_title("Where each candidate's score comes from", fontsize=14, weight="bold")
    ax.legend(loc="lower right", fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
