"""
Recruiter dashboard for the Automated Resume Screening Tool.

Run:  streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.matcher import DEFAULT_WEIGHTS, REVIEW_SCORE, SHORTLIST_SCORE
from src.parser import load_skill_dictionary, pretty
from src.report import excel_bytes, feedback_text
from src.screener import load_jobs, screen_folder, screen_uploads, to_dataframe

ROOT = Path(__file__).resolve().parent
COLOURS = {"Shortlisted": "#16A34A", "Review": "#F59E0B", "Rejected": "#DC2626"}

st.set_page_config(page_title="Resume Screening Tool", page_icon="🧑‍💼", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.6rem;}
.hero {background: linear-gradient(120deg, #1E3A8A 0%, #2563EB 60%, #38BDF8 100%); color: white;
       padding: 1.4rem 1.8rem; border-radius: 16px; margin-bottom: 1.2rem;}
.hero h1 {margin: 0; font-size: 2rem; color: white;}
.hero p {margin: .3rem 0 0 0; opacity: .9;}
.kpi {background: white; border: 1px solid #E5E7EB; border-radius: 14px; padding: 1rem 1.2rem;
      box-shadow: 0 1px 3px rgba(0,0,0,.06);}
.kpi .label {color: #6B7280; font-size: .85rem; text-transform: uppercase; letter-spacing: .04em;}
.kpi .value {font-size: 1.9rem; font-weight: 700; color: #111827;}
.kpi .sub {color: #6B7280; font-size: .85rem;}
.chip {display: inline-block; padding: .2rem .65rem; margin: .15rem; border-radius: 999px; font-size: .85rem;}
.chip.ok {background: #DCFCE7; color: #166534;}
.chip.miss {background: #FEE2E2; color: #991B1B;}
.chip.bonus {background: #DBEAFE; color: #1E40AF;}
.badge {padding: .25rem .8rem; border-radius: 999px; color: white; font-weight: 600;}
</style>
""", unsafe_allow_html=True)


def kpi(col, label: str, value: str, sub: str = "") -> None:
    col.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div>'
                 f'<div class="sub">{sub}</div></div>', unsafe_allow_html=True)


def chips(skills: list[str], kind: str) -> str:
    if not skills:
        return '<span style="color:#9CA3AF">none</span>'
    return "".join(f'<span class="chip {kind}">{pretty(s)}</span>' for s in skills)


# ------------------------------------------------------------------ sidebar
jobs = load_jobs()
dictionary = load_skill_dictionary()
all_skills = sorted({skill for cat in dictionary.values() for skill in cat})

with st.sidebar:
    st.header("1. Job description")
    job_choice = st.selectbox("Choose a job", list(jobs) + ["custom"],
                              format_func=lambda j: jobs[j]["title"] if j in jobs else "✏️ Write my own")
    base = jobs.get(job_choice, {"id": "custom", "title": "Custom Role", "company": "My Company",
                                 "location": "-", "min_experience": 1, "education": "bachelor",
                                 "must_have": ["python"], "nice_to_have": [], "description": ""})
    title = st.text_input("Job title", base["title"])
    description = st.text_area("Job description", base["description"], height=160)
    must_have = st.multiselect("Must-have skills", all_skills, default=base["must_have"], format_func=pretty)
    nice_to_have = st.multiselect("Nice-to-have skills", [s for s in all_skills if s not in must_have],
                                  default=[s for s in base["nice_to_have"] if s not in must_have], format_func=pretty)
    min_exp = st.slider("Minimum experience (years)", 0.0, 10.0, float(base["min_experience"]), 0.5)

    with st.expander("⚖️ Scoring weights"):
        weights = {k: st.slider(k.replace("_", " ").title(), 0.0, 1.0, v, 0.05) for k, v in DEFAULT_WEIGHTS.items()}
        st.caption("Weights are normalised automatically, so they don't have to add up to 1.")

    st.header("2. Resumes")
    source = st.radio("Resume source", ["Sample resumes (10)", "Upload my own"], label_visibility="collapsed")
    uploads = None
    if source == "Upload my own":
        uploads = st.file_uploader("PDF, DOCX or TXT", type=["pdf", "docx", "txt"], accept_multiple_files=True)

job = {**base, "id": base["id"], "title": title, "description": description, "must_have": must_have,
       "nice_to_have": nice_to_have, "min_experience": min_exp}

st.markdown(f'<div class="hero"><h1>🧑‍💼 Automated Resume Screening</h1>'
            f'<p>Ranking candidates for <b>{title}</b> · {job.get("company", "")} · '
            f'{len(must_have)} must-have skills · {min_exp:g}+ years</p></div>', unsafe_allow_html=True)

if not must_have:
    st.warning("Add at least one must-have skill in the sidebar.")
    st.stop()


@st.cache_data(show_spinner="Reading and scoring resumes...")
def run_screening(job_items: tuple, weight_items: tuple, files: tuple | None):
    job_dict = {k: list(v) if isinstance(v, tuple) else v for k, v in job_items}
    w = dict(weight_items)
    candidates = screen_uploads(job_dict, list(files), w) if files else screen_folder(job_dict, ROOT / "resumes", w)
    return candidates


frozen_job = tuple((k, tuple(v) if isinstance(v, list) else v) for k, v in job.items())
files = tuple((f.name, f.getvalue()) for f in uploads) if uploads else None
if source == "Upload my own" and not files:
    st.info("⬅️ Upload one or more resumes in the sidebar to start screening.")
    st.stop()

candidates = run_screening(frozen_job, tuple(weights.items()), files)
df = to_dataframe(candidates)
counts = df["Decision"].value_counts()

# ------------------------------------------------------------------ KPIs
c1, c2, c3, c4 = st.columns(4)
kpi(c1, "Resumes screened", str(len(df)), "PDF · DOCX · TXT")
kpi(c2, "Shortlisted", str(counts.get("Shortlisted", 0)), f"{counts.get('Review', 0)} need manual review")
kpi(c3, "Average score", f"{df['Score'].mean():.1f}", f"best {df['Score'].max():.1f}")
kpi(c4, "Top candidate", df.iloc[0]["Candidate"], f"{df.iloc[0]['Score']:.1f}/100")
st.write("")

tab_overview, tab_rank, tab_profile, tab_gap, tab_export = st.tabs(
    ["📊 Overview", "🏆 Ranking", "👤 Candidate profile", "🧩 Skill gaps", "📥 Export"])

with tab_overview:
    left, right = st.columns([2, 1])
    data = df.sort_values("Score")
    fig = px.bar(data, x="Score", y="Candidate", orientation="h", color="Decision", color_discrete_map=COLOURS,
                 text="Score", category_orders={"Decision": list(COLOURS)}, hover_data=["Must-have %", "Experience (yrs)", "Missing must-have"])
    fig.add_vline(SHORTLIST_SCORE, line_dash="dash", line_color=COLOURS["Shortlisted"], annotation_text="Shortlist")
    fig.add_vline(REVIEW_SCORE, line_dash="dot", line_color=COLOURS["Review"], annotation_text="Review")
    fig.update_layout(height=430, title="Candidate ranking", xaxis_range=[0, 105], legend_title=None,
                      margin=dict(l=10, r=10, t=50, b=10))
    left.plotly_chart(fig, width="stretch")

    donut = px.pie(df, names="Decision", hole=.55, color="Decision", color_discrete_map=COLOURS, title="Decisions",
                   category_orders={"Decision": list(COLOURS)})
    donut.update_layout(height=430, showlegend=True, margin=dict(l=10, r=10, t=50, b=10))
    right.plotly_chart(donut, width="stretch")

    scatter = px.scatter(df, x="Experience (yrs)", y="Score", size="Must-have %", color="Decision",
                         color_discrete_map=COLOURS, hover_name="Candidate", size_max=28,
                         category_orders={"Decision": list(COLOURS)},
                         title="Score vs experience (bubble size = must-have coverage)")
    scatter.update_layout(height=380, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(scatter, width="stretch")

with tab_rank:
    pick = st.multiselect("Show decisions", list(COLOURS), default=list(COLOURS))
    view = df[df["Decision"].isin(pick)]
    st.dataframe(
        view[["Rank", "Candidate", "Score", "Decision", "Must-have %", "Similarity %", "Experience (yrs)",
              "Education", "Missing must-have", "Bonus skills", "Flags", "File"]],
        hide_index=True, width="stretch", height=420,
        column_config={
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.1f"),
            "Must-have %": st.column_config.ProgressColumn("Must-have", min_value=0, max_value=100, format="%d%%"),
            "Similarity %": st.column_config.NumberColumn("Similarity", format="%d%%"),
        })

with tab_profile:
    names = [f"#{i + 1} {c.parsed.name}" for i, c in enumerate(candidates)]
    idx = st.selectbox("Candidate", range(len(candidates)), format_func=lambda i: names[i])
    cand = candidates[idx]
    m, p = cand.match, cand.parsed

    head_l, head_r = st.columns([3, 1])
    head_l.subheader(p.name)
    head_l.caption(f"{cand.file} · {p.email or 'no email'} · {p.phone or 'no phone'}")
    head_r.markdown(f'<div style="text-align:right;margin-top:.6rem"><span class="badge" '
                    f'style="background:{COLOURS[m.decision]}">{m.decision} · {m.score:.1f}</span></div>',
                    unsafe_allow_html=True)

    col_radar, col_info = st.columns([1, 1])
    labels = [k.replace("_", " ").title() for k in m.components]
    values = [100 * v for v in m.components.values()]
    radar = go.Figure(go.Scatterpolar(r=values + values[:1], theta=labels + labels[:1], fill="toself",
                                      line_color="#2563EB", name=p.name))
    radar.update_layout(polar=dict(radialaxis=dict(range=[0, 100])), height=380, showlegend=False,
                        title="Score components (0-100)", margin=dict(l=40, r=40, t=50, b=20))
    col_radar.plotly_chart(radar, width="stretch")

    with col_info:
        st.markdown("**✅ Must-have skills matched**")
        st.markdown(chips(m.must_have_matched, "ok"), unsafe_allow_html=True)
        st.markdown("**❌ Must-have skills missing**")
        st.markdown(chips(m.must_have_missing, "miss"), unsafe_allow_html=True)
        st.markdown("**⭐ Nice-to-have skills**")
        st.markdown(chips(m.nice_to_have_matched, "bonus"), unsafe_allow_html=True)
        st.markdown(f"**🎓 Education:** {(p.education or 'not found').title()} &nbsp;&nbsp; "
                    f"**💼 Experience:** {p.years_experience:g} years")
        for reason in m.reasons:
            st.success(reason, icon="✔️")
        for flag in m.flags:
            st.warning(flag, icon="⚠️")

    with st.expander("All skills found, by category"):
        for category, skills in p.skill_categories.items():
            st.markdown(f"**{category}:** " + chips(skills, "bonus"), unsafe_allow_html=True)

with tab_gap:
    skills = must_have + nice_to_have
    grid = pd.DataFrame([[1 if s in c.parsed.skills else 0 for s in skills] for c in candidates],
                        index=[c.parsed.name for c in candidates], columns=[pretty(s) for s in skills])
    heat = px.imshow(grid, color_continuous_scale=[[0, "#FECACA"], [1, "#BBF7D0"]], aspect="auto",
                     title="Who has which skill? (green = found)")
    heat.update_traces(text=grid.replace({1: "✓", 0: "✗"}).values, texttemplate="%{text}", hovertemplate=None)
    heat.update_layout(coloraxis_showscale=False, height=460, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(heat, width="stretch")

    coverage = pd.DataFrame({"Skill": [pretty(s) for s in skills],
                             "Candidates with skill": grid.sum().values,
                             "Type": ["Must-have"] * len(must_have) + ["Nice-to-have"] * len(nice_to_have)})
    bar = px.bar(coverage.sort_values("Candidates with skill"), x="Candidates with skill", y="Skill", color="Type",
                 orientation="h", title="How common is each required skill in the applicant pool?",
                 color_discrete_map={"Must-have": "#1E3A8A", "Nice-to-have": "#60A5FA"})
    bar.update_layout(height=380, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(bar, width="stretch")
    rare = coverage[(coverage["Type"] == "Must-have") & (coverage["Candidates with skill"] <= len(df) * 0.3)]
    if not rare.empty:
        st.info("Hard-to-find must-have skills: " + ", ".join(rare["Skill"]) +
                ". Consider moving them to nice-to-have or offering training.")

with tab_export:
    st.subheader("Download the results")
    d1, d2, d3 = st.columns(3)
    d1.download_button("⬇️ Full report (CSV)", df.to_csv(index=False), f"{job['id']}_screening_report.csv",
                       "text/csv", width="stretch")
    d2.download_button("⬇️ Formatted report (Excel)", excel_bytes(df, job), f"{job['id']}_screening_report.xlsx",
                       width="stretch")
    d3.download_button("⬇️ Candidate feedback (TXT)", feedback_text(candidates, job),
                       f"{job['id']}_candidate_feedback.txt", width="stretch")
    st.dataframe(df[df["Decision"] == "Shortlisted"][["Rank", "Candidate", "Score", "Email", "File"]],
                 hide_index=True, width="stretch")
    st.caption("Personal details (email, phone) are removed before scoring, so they never affect the result.")
