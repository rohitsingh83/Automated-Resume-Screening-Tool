"""Modern, interactive Streamlit dashboard for Automated Resume Screening."""
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="AI Resume Screening & ATS Ranking",
    page_icon="📄",
    layout="wide",
)

st.title("📄 AI Resume Screening & ATS Ranking Hub")
st.caption("Automated NLP Candidate Scoring, Skill Gap Analysis & Shortlisting")

csv_path = ROOT / "outputs" / "screening_results.csv"
chart_path = ROOT / "images" / "candidate_ranking_chart.png"

# Sidebar
with st.sidebar:
    st.header("⚙️ ATS Configuration")
    st.markdown("**Thresholds:**")
    st.info("Shortlist Cutoff: **0.55**\n\nMin Must-Have Match: **60%**")
    st.markdown("---")
    st.markdown("### 🔍 Model & Architecture")
    st.markdown("- **Parser:** PDF, DOCX, TXT")
    st.markdown("- **NLP:** TF-IDF & Cosine Similarity")
    st.markdown("- **Storage:** SQLite 3")
    st.markdown("- **API:** FastAPI (`/rank`)")

if csv_path.exists():
    df = pd.read_csv(csv_path)

    # Key Performance Metrics
    c1, c2, c3, c4 = st.columns(4)
    total_cand = len(df)
    shortlisted_cand = int((df["status"] == "Shortlisted").sum())
    rejected_cand = total_cand - shortlisted_cand
    top_score = df["final_score"].max() if "final_score" in df else 0.0

    c1.metric("Total Resumes", total_cand)
    c2.metric("Shortlisted Candidates", shortlisted_cand, delta=f"{(shortlisted_cand/max(1, total_cand)*100):.0f}% rate")
    c3.metric("Under Review / Rejected", rejected_cand)
    c4.metric("Top Candidate Score", f"{top_score:.2f}")

    st.markdown("---")

    # Filter Controls
    f_col1, f_col2 = st.columns([1, 2])
    with f_col1:
        status_filter = st.radio("Status Filter:", ["All", "Shortlisted", "Rejected"], horizontal=True)

    filtered_df = df if status_filter == "All" else df[df["status"] == status_filter]

    st.subheader(f"📋 Candidate Ranking Table ({len(filtered_df)} profiles)")
    
    # Custom display table
    display_cols = [c for c in ["candidate_name", "final_score", "must_have_ratio", "years_experience", "education", "status", "missing_must_have"] if c in df.columns]
    st.dataframe(filtered_df[display_cols], use_container_width=True)

    # Detailed Candidate Cards
    st.markdown("### 🔎 Candidate Detailed Breakdown")
    for _, row in filtered_df.iterrows():
        is_shortlisted = row.get("status") == "Shortlisted"
        badge = "🟢 SHORTLISTED" if is_shortlisted else "🔴 REJECTED"
        expander_title = f"{row.get('candidate_name', 'Unknown')} — Score: {row.get('final_score', 0):.2f} [{badge}]"
        
        with st.expander(expander_title):
            co1, co2, co3 = st.columns(3)
            co1.markdown(f"**Education:** {row.get('education', 'N/A')}")
            co1.markdown(f"**Experience:** {row.get('years_experience', 0)} years")
            co2.markdown(f"**TF-IDF Similarity:** {row.get('similarity_score', 0):.3f}")
            co2.markdown(f"**Must-Have Match:** {row.get('must_have_ratio', 0)*100:.1f}%")
            co3.markdown(f"**Matched Skills:** {row.get('matched_must_have', 'None')}")
            co3.markdown(f"**Missing Critical Skills:** `{row.get('missing_must_have', 'None')}`")
            st.info(f"**Reasoning:** {row.get('explanation', 'No explanation provided.')}")

    # Visual Chart
    if chart_path.exists():
        st.markdown("---")
        st.subheader("📊 Candidate Ranking Visualization")
        st.image(str(chart_path), caption="Rankings against 0.55 Shortlist Threshold", use_container_width=True)
else:
    st.warning("No screening results found. Run `python main.py` to trigger the ATS screening pipeline.")
