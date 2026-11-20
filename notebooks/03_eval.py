"""Evaluation script computing Top-K Precision and accuracy on labeled_pairs.csv."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
df = pd.read_csv(ROOT / "data" / "labeled_pairs.csv")
df["pred"] = (df["score"] >= 0.55).astype(int)
accuracy = (df["pred"] == df["label"]).mean()
top3_prec = df.sort_values("score", ascending=False).head(3)["label"].mean()
print(f"Evaluation Accuracy: {accuracy:.2%} | Top-3 Precision: {top3_prec:.2%}")
