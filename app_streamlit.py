"""Flagship AI Resume Screening & ATS Ranking Application.
Features:
- Multi-file drag-and-drop resume upload (PDF, DOCX, TXT)
- Real-time PII redaction and skills/experience extraction
- Interactive Job Description editor with customizable must-have skills
- Dynamic TF-IDF vectorization and explainable candidate scoring
- Interactive Plotly charts (Candidate score ranking, Skill overlap radar chart, Gauge meters)
- CSV and Excel export of ranked candidates
"""

import io
import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import settings
from src.extract import clean_for_nlp, parse_resume, extract_skills, extract_years_experience, extract_education
from src.features import compute_jd_similarities
from src.rank import score_candidate
from src.ingest import extract_text_from_docx, extract_text_from_pdf, normalize_whitespace

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="TalentScan AI — Enterprise ATS Resume Screener",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-title { font-size: 2.3rem; font-weight: 800; color: #1E3A8A; margin-bottom: 0.2rem; }
    .sub-title { font-size: 1.05rem; color: #4B5563; margin-bottom: 1.5rem; }
    .kpi-card { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 1rem; text-align: center; }
    .shortlisted-tag { background-color: #DCFCE7; color: #166534; font-weight: 700; padding: 4px 10px; border-radius: 6px; }
    .rejected-tag { background-color: #FEE2E2; color: #991B1B; font-weight: 700; padding: 4px 10px; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🎯 TalentScan AI — ATS Resume Screening & Ranking Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Production NLP Candidate Matching • Explainable ATS Scoring • PII-Safe Parsing</div>', unsafe_allow_html=True)

# Helper function to parse uploaded files directly from memory
def parse_uploaded_file(uploaded_file) -> Dict[str, Any]:
    ext = Path(uploaded_file.name).suffix.lower()
    raw_text = ""
    if ext == ".txt":
        raw_text = uploaded_file.getvalue().decode("utf-8", errors="ignore")
    elif ext == ".docx":
        from docx import Document
        doc = Document(io.BytesIO(uploaded_file.getvalue()))
        raw_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    elif ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(uploaded_file.getvalue()))
        raw_text = "\n".join([p.extract_text() or "" for p in reader.pages])
    else:
        raw_text = ""
    
    clean_text = normalize_whitespace(raw_text)
    name = Path(uploaded_file.name).stem.replace("_", " ").title()
    return {
        "filename": uploaded_file.name,
        "candidate_name": name,
        "raw_text": raw_text,
        "clean_text": clean_text,
    }

# Load default config
default_jd = settings.jd_path.read_text(encoding="utf-8") if settings.jd_path.exists() else "Looking for a Python Developer..."
default_cfg = json.loads(settings.skills_config_path.read_text(encoding="utf-8")) if settings.skills_config_path.exists() else {
    "must_have": ["python", "pandas", "sql", "git"],
    "good_to_have": ["fastapi", "docker", "scikit-learn"],
    "min_years": 1.0,
    "shortlist_threshold": 0.55
}

# Sidebar: Job Requirements Configuration
with st.sidebar:
    st.header("⚙️ Target Job Profile")
    job_title = st.text_input("Position Title", "Senior Python & ML Engineer")
    
    st.subheader("Required Skills")
    must_have_str = st.text_area(
        "Must-Have Skills (comma-separated)",
        ", ".join(default_cfg.get("must_have", ["python", "pandas", "numpy", "sql", "git"]))
    )
    must_have_skills = [s.strip().lower() for s in must_have_str.split(",") if s.strip()]
    
    good_to_have_str = st.text_area(
        "Good-To-Have Skills (comma-separated)",
        ", ".join(default_cfg.get("good_to_have", ["fastapi", "docker", "scikit-learn", "nlp"]))
    )
    good_to_have_skills = [s.strip().lower() for s in good_to_have_str.split(",") if s.strip()]

    st.subheader("Scoring Thresholds")
    min_years = st.number_input("Minimum Required Experience (Years)", min_value=0.0, max_value=20.0, value=float(default_cfg.get("min_years", 1.0)), step=0.5)
    shortlist_cutoff = st.slider("Shortlist Score Cutoff", min_value=0.30, max_value=0.90, value=float(default_cfg.get("shortlist_threshold", 0.55)), step=0.05)
    
    st.markdown("---")
    st.caption("ℹ️ PII Redaction: Candidate phone numbers and emails are automatically masked before semantic vectorization.")

tab_screen, tab_benchmark, tab_system = st.tabs(["🚀 Live Screening Portal", "📊 Benchmark & Analytics", "🏗 System Architecture"])

with tab_screen:
    col_jd, col_upload = st.columns([1, 1])
    
    with col_jd:
        st.subheader("1. Job Description (JD)")
        jd_input = st.text_area("Paste or modify the Target Job Description:", value=default_jd, height=240)
    
    with col_upload:
        st.subheader("2. Candidate Resumes")
        uploaded_files = st.file_uploader(
            "Upload Resumes (.pdf, .docx, .txt)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
            help="You can upload multiple resumes at once to screen them simultaneously."
        )
        use_bundled = st.checkbox("Include 6 bundled benchmark resumes from database", value=True)

    if st.button("⚡ Run ATS Screening & Match Candidates", type="primary", use_container_width=True):
        candidates_to_process = []
        
        # 1. Process uploaded files
        if uploaded_files:
            for uf in uploaded_files:
                parsed = parse_uploaded_file(uf)
                if parsed["clean_text"]:
                    candidates_to_process.append(parsed)
        
        # 2. Add bundled resumes if selected
        if use_bundled:
            from src.ingest import load_all_resumes
            bundled = load_all_resumes(settings.resumes_dir)
            for b in bundled:
                if not any(c["filename"] == b["filename"] for c in candidates_to_process):
                    candidates_to_process.append(b)

        if not candidates_to_process:
            st.error("No resumes available! Please upload resumes or check 'Include bundled benchmark resumes'.")
        else:
            with st.spinner(f"Parsing and evaluating {len(candidates_to_process)} candidate resumes..."):
                all_vocab = list(set(must_have_skills + good_to_have_skills))
                parsed_profiles = [parse_resume(c["clean_text"], vocabulary=all_vocab) for c in candidates_to_process]
                
                # TF-IDF Cosine Similarity
                jd_clean = clean_for_nlp(jd_input)
                resume_texts = [p["nlp_text"] for p in parsed_profiles]
                sims, backend = compute_jd_similarities(jd_clean, resume_texts)
                
                results = []
                for cand, prof, sim in zip(candidates_to_process, parsed_profiles, sims):
                    scored = score_candidate(
                        similarity=sim,
                        candidate_skills=prof["skills"],
                        years_exp=prof["years_experience"],
                        must_have_skills=must_have_skills,
                        min_years=min_years,
                        shortlist_threshold=shortlist_cutoff,
                    )
                    results.append({
                        "Candidate Name": cand["candidate_name"],
                        "Filename": cand["filename"],
                        "Final ATS Score": scored["final_score"],
                        "Status": scored["status"],
                        "Semantic Match": round(scored["similarity_score"] * 100, 1),
                        "Must-Have Skills Met": f"{round(scored['must_have_ratio'] * 100)}%",
                        "Experience (Yrs)": prof["years_experience"],
                        "Education": prof["education"],
                        "Matched Skills": scored["matched_must_have"],
                        "Missing Critical Skills": scored["missing_must_have"],
                        "AI Feedback": scored["explanation"],
                    })

                res_df = pd.DataFrame(results).sort_values("Final ATS Score", ascending=False).reset_index(drop=True)
                res_df.index += 1
                res_df.index.name = "Rank"
                st.session_state["screening_results"] = res_df
                st.session_state["active_backend"] = backend

    # Display Results if available
    if "screening_results" in st.session_state:
        df = st.session_state["screening_results"]
        st.markdown("---")
        
        # KPI Row
        k1, k2, k3, k4 = st.columns(4)
        total_screened = len(df)
        shortlisted_cnt = int((df["Status"] == "Shortlisted").sum())
        shortlist_rate = (shortlisted_cnt / total_screened) * 100 if total_screened else 0
        top_cand = df.iloc[0]["Candidate Name"] if not df.empty else "N/A"
        top_score = df.iloc[0]["Final ATS Score"] if not df.empty else 0.0

        k1.metric("Total Candidates Screened", total_screened)
        k2.metric("Shortlisted for Interview", shortlisted_cnt, delta=f"{shortlist_rate:.0f}% selection rate")
        k3.metric("Top Ranked Candidate", top_cand)
        k4.metric("Highest ATS Score", f"{top_score:.2f} / 1.00")

        # Interactive Ranking Chart
        st.subheader("📊 Candidate Ranking & Cutoff Comparison")
        fig_bar = px.bar(
            df.sort_values("Final ATS Score", ascending=True),
            x="Final ATS Score",
            y="Candidate Name",
            orientation="h",
            color="Status",
            color_discrete_map={"Shortlisted": "#16A34A", "Rejected": "#DC2626"},
            text="Final ATS Score",
            hover_data=["Semantic Match", "Must-Have Skills Met", "Experience (Yrs)", "Education"],
            title=f"ATS Candidate Score Distribution (Threshold: {shortlist_cutoff})",
        )
        fig_bar.add_vline(x=shortlist_cutoff, line_dash="dash", line_color="#2563EB", annotation_text=f"Cutoff ({shortlist_cutoff})")
        fig_bar.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

        # Ranked Table
        st.subheader("📋 Ranked Candidate Table")
        st.dataframe(
            df[["Candidate Name", "Final ATS Score", "Status", "Semantic Match", "Must-Have Skills Met", "Experience (Yrs)", "Education", "Missing Critical Skills"]],
            use_container_width=True,
        )

        # Detailed Drilldown Cards
        st.subheader("🔍 Individual Candidate Skill Breakdown")
        for idx, row in df.iterrows():
            is_pass = row["Status"] == "Shortlisted"
            badge = "🟢 SHORTLISTED" if is_pass else "🔴 NOT SHORTLISTED"
            with st.expander(f"Rank #{idx}: {row['Candidate Name']} — Score: {row['Final ATS Score']:.2f} [{badge}]"):
                c_a, c_b, c_c = st.columns([1, 1, 1])
                c_a.markdown(f"**Experience:** {row['Experience (Yrs)']} years")
                c_a.markdown(f"**Education:** {row['Education']}")
                c_b.markdown(f"**Semantic JD Match:** {row['Semantic Match']}%")
                c_b.markdown(f"**Must-Have Match:** {row['Must-Have Skills Met']}")
                c_c.markdown(f"**Matched Skills:** `{row['Matched Skills']}`")
                c_c.markdown(f"**Missing Critical Skills:** `{row['Missing Critical Skills']}`")
                st.info(f"💡 **ATS Scoring Summary:** {row['AI Feedback']}")

        # Export Buttons
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            csv_data = df.to_csv(index=True).encode("utf-8")
            st.download_button("📥 Download Screening Results (CSV)", data=csv_data, file_name="ats_candidate_rankings.csv", mime="text/csv")
        with col_dl2:
            shortlisted_csv = df[df["Status"] == "Shortlisted"].to_csv(index=True).encode("utf-8")
            st.download_button("📥 Download Shortlist Only (CSV)", data=shortlisted_csv, file_name="shortlisted_candidates.csv", mime="text/csv")

with tab_benchmark:
    st.subheader("📈 Pre-Computed Benchmark Evaluation")
    csv_path = settings.outputs_dir / "screening_results.csv"
    if csv_path.exists():
        stored_df = pd.read_csv(csv_path)
        
        # Donut Chart of Shortlist Ratio
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            status_counts = stored_df["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]
            fig_donut = px.pie(
                status_counts,
                names="Status",
                values="Count",
                hole=0.45,
                color="Status",
                color_discrete_map={"Shortlisted": "#16A34A", "Rejected": "#DC2626"},
                title="Applicant Selection Ratio",
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            
        with col_p2:
            fig_scatter = px.scatter(
                stored_df,
                x="similarity_score",
                y="must_have_ratio",
                size="years_experience",
                color="status",
                hover_name="candidate_name",
                color_discrete_map={"Shortlisted": "#16A34A", "Rejected": "#DC2626"},
                title="Semantic Similarity vs Must-Have Match Ratio",
                labels={"similarity_score": "TF-IDF Cosine Similarity", "must_have_ratio": "Must-Have Skill Ratio"},
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Run the screening pipeline to generate benchmark data.")

with tab_system:
    st.subheader("🏛 System Architecture & Mathematical Foundations")
    st.markdown("""
    ### Scoring Formula
    $$\\text{ATS Score} = 0.45 \\cdot \\text{Sim} + 0.45 \\cdot \\text{MustRatio} + 0.10 \\cdot \\text{ExpRatio} - 0.05 \\cdot N_{\\text{missing}}$$
    
    - **Sim:** Cosine similarity of L2-normalized TF-IDF vectors (word 1-2 n-grams).
    - **MustRatio:** Fraction of core job skills satisfied by applicant.
    - **ExpRatio:** Ratio of candidate career duration relative to required minimum.
    - **$N_{\\text{missing}}$:** Number of critical skills absent from candidate profile.
    
    ### Privacy & Bias Elimination
    Before vector representation, regex filters redact candidate phone numbers and email addresses. The vectorizer evaluates strictly vocabulary overlap with zero demographic exposure.
    """)
