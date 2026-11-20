"""Interactive Streamlit dashboard for Automated Resume Screening Tool."""
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Automated Resume Screening Tool", layout="wide", page_icon="📄")
st.title("📄 Automated Resume Screening Tool")

csv_path = ROOT / "outputs" / "screening_results.csv"
chart_path = ROOT / "images" / "candidate_ranking_chart.png"

if csv_path.exists():
    df = pd.read_csv(csv_path)
    
    # Overview Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Candidates", len(df))
    shortlisted_count = int((df["status"] == "Shortlisted").sum())
    c2.metric("Shortlisted", shortlisted_count)
    rejected_count = len(df) - shortlisted_count
    c3.metric("Rejected", rejected_count)
    top_score = df["final_score"].max() if "final_score" in df else 0.0
    c4.metric("Top ATS Score", f"{top_score:.2f}")

    # Status Filter
    st.markdown("---")
    status_filter = st.selectbox("Filter by Status", ["All", "Shortlisted", "Rejected"])
    filtered_df = df if status_filter == "All" else df[df["status"] == status_filter]
    
    st.subheader("📋 Candidate Rankings & Explanations")
    st.dataframe(filtered_df, use_container_width=True)

    # Ranking Chart
    if chart_path.exists():
        st.subheader("📊 Candidate Ranking Visualization")
        st.image(str(chart_path), caption="Candidate ATS Matching Scores & Shortlist Cutoff", use_container_width=True)
else:
    st.info("No screening results found. Run `python main.py` first to generate screening results.")
