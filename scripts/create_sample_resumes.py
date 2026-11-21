"""
Create realistic sample resumes (PDF, DOCX and TXT) for testing the screener.

We do not have access to a real company's applicant data, so this script
generates 10 fictional candidates with different skill levels. Each resume
has the usual sections: contact details, summary, skills, experience,
education and projects.

Run:  python scripts/create_sample_resumes.py
"""

from pathlib import Path

from docx import Document
from docx.shared import Pt
from fpdf import FPDF

RESUME_DIR = Path(__file__).resolve().parent.parent / "resumes"

CANDIDATES = [
    {
        "file": "aarav_mehta.pdf",
        "name": "Aarav Mehta",
        "email": "aarav.mehta@example.com",
        "phone": "+91 98450 11223",
        "summary": "Data Analyst with 3 years of experience turning sales data into dashboards and business insights.",
        "skills": "Python, Pandas, NumPy, SQL (PostgreSQL, MySQL), Advanced Excel (Pivot Tables, VLOOKUP), Power BI, Tableau, Statistics, A/B Testing, Data Visualization (Matplotlib, Seaborn), Communication",
        "experience": [
            ("Data Analyst, ShopKart India", "Jun 2022 - Present",
             "Built Power BI dashboards tracking revenue for 120 stores; automated weekly Excel reports with Python and Pandas, saving 6 hours per week; wrote SQL queries on a 40M-row sales table."),
            ("Junior Analyst, Numero Consulting", "Jul 2021 - May 2022",
             "Cleaned survey data, ran hypothesis tests and presented findings to clients."),
        ],
        "education": "B.Tech in Computer Science, VIT Vellore, 2021 (CGPA 8.4)",
        "projects": "Customer churn analysis (Python, scikit-learn); Retail sales dashboard (Power BI).",
    },
    {
        "file": "diya_sharma.docx",
        "name": "Diya Sharma",
        "email": "diya.sharma@example.com",
        "phone": "+91 99001 45678",
        "summary": "Machine Learning Engineer with 4 years of experience building NLP and recommendation models in production.",
        "skills": "Python, SQL, Pandas, scikit-learn, Machine Learning, Deep Learning, PyTorch, TensorFlow, NLP (spaCy, NLTK), LLM, LangChain, Docker, AWS (S3, EC2, Lambda), Git, Statistics",
        "experience": [
            ("ML Engineer, Zentro AI", "Jan 2022 - Present",
             "Trained transformer-based NLP models in PyTorch for ticket classification (F1 0.91); deployed models as Docker containers on AWS; built an LLM-powered FAQ bot with LangChain."),
            ("Data Scientist, FinEdge", "Aug 2020 - Dec 2021",
             "Built credit-risk models with scikit-learn and feature pipelines in SQL and Pandas."),
        ],
        "education": "M.Tech in Artificial Intelligence, IIIT Hyderabad, 2020",
        "projects": "Resume parser using spaCy NER; Image classifier with CNNs (TensorFlow).",
    },
    {
        "file": "kabir_singh.txt",
        "name": "Kabir Singh",
        "email": "kabir.singh@example.com",
        "phone": "+91 97311 98765",
        "summary": "Backend developer with 3+ years of experience building REST APIs in Python and Django.",
        "skills": "Python, Django, Django REST Framework, FastAPI, REST API, PostgreSQL, SQL, Git, GitHub Actions, Docker, Linux, Bash, AWS EC2, Teamwork",
        "experience": [
            ("Software Engineer, PayLoop", "Mar 2022 - Present",
             "Designed REST APIs in Django serving 2M requests/day; migrated services to FastAPI; set up CI/CD with GitHub Actions and Docker."),
            ("Associate Developer, CodeCraft", "Jun 2020 - Feb 2022",
             "Built internal tools with Flask and PostgreSQL; wrote unit tests and code reviews on GitHub."),
        ],
        "education": "B.E. in Information Technology, Pune University, 2020",
        "projects": "Expense tracker API (FastAPI, SQLite); URL shortener (Django, Redis).",
    },
    {
        "file": "ananya_iyer.pdf",
        "name": "Ananya Iyer",
        "email": "ananya.iyer@example.com",
        "phone": "+91 90080 33445",
        "summary": "Final-year student passionate about data analytics, looking for an entry-level analyst role.",
        "skills": "Python, Pandas, SQL, Excel, Data Visualization (Matplotlib), Statistics, Communication, Teamwork",
        "experience": [
            ("Data Analytics Intern, GreenLeaf Foods", "Jan 2025 - Jun 2025",
             "Analysed sales data in Excel and Python; built charts for monthly review meetings."),
        ],
        "education": "B.Sc. in Statistics, Christ University, 2025",
        "projects": "COVID-19 data analysis (Pandas, Matplotlib); IPL score predictor (scikit-learn).",
    },
    {
        "file": "rohan_gupta.docx",
        "name": "Rohan Gupta",
        "email": "rohan.gupta@example.com",
        "phone": "+91 98860 77889",
        "summary": "Full-stack developer with 2 years of experience in JavaScript, React and Node.",
        "skills": "JavaScript, React, Node.js, HTML, CSS, MongoDB, Git, REST API, Teamwork",
        "experience": [
            ("Frontend Developer, PixelWorks", "Aug 2023 - Present",
             "Built React dashboards and REST API integrations for e-commerce clients."),
            ("Web Developer Intern, StartHub", "Jan 2023 - Jul 2023",
             "Created responsive landing pages in HTML, CSS and JavaScript."),
        ],
        "education": "B.Tech in Electronics, NIT Trichy, 2023",
        "projects": "Chat app (React, Socket.io); Portfolio website.",
    },
    {
        "file": "meera_nair.txt",
        "name": "Meera Nair",
        "email": "meera.nair@example.com",
        "phone": "+91 94470 12121",
        "summary": "Business Intelligence analyst with 5 years of experience in SQL, Tableau and stakeholder reporting.",
        "skills": "SQL, T-SQL, Excel, Tableau, Power BI, Statistics, Communication, Stakeholder Management, Leadership, Python (basic)",
        "experience": [
            ("Senior BI Analyst, Horizon Insurance", "Apr 2021 - Present",
             "Led a team of 3 analysts; built Tableau executive dashboards; wrote complex SQL for claims analytics."),
            ("BI Analyst, DataWave", "Jul 2019 - Mar 2021",
             "Created Excel and Power BI reports for operations teams."),
        ],
        "education": "MBA in Business Analytics, NMIMS Mumbai, 2019; B.Com, 2017",
        "projects": "Claims fraud early-warning dashboard (Tableau).",
    },
    {
        "file": "arjun_reddy.pdf",
        "name": "Arjun Reddy",
        "email": "arjun.reddy@example.com",
        "phone": "+91 99490 56565",
        "summary": "Data scientist with 2 years of experience in machine learning, statistics and Python.",
        "skills": "Python, Pandas, NumPy, scikit-learn, Machine Learning, Statistics, SQL, TensorFlow, Data Visualization, Git, Problem Solving",
        "experience": [
            ("Data Scientist, RetailIQ", "Jul 2023 - Present",
             "Built demand-forecasting models with scikit-learn and TensorFlow; reduced stock-outs by 12%."),
            ("ML Intern, Quantify Labs", "Jan 2023 - Jun 2023",
             "Cleaned data and trained classification models in Python."),
        ],
        "education": "B.Tech in Computer Science, JNTU Hyderabad, 2023",
        "projects": "Movie recommender (collaborative filtering); Sentiment analysis (NLP, NLTK).",
    },
    {
        "file": "sneha_kapoor.docx",
        "name": "Sneha Kapoor",
        "email": "sneha.kapoor@example.com",
        "phone": "+91 98100 24680",
        "summary": "HR operations executive moving into people analytics.",
        "skills": "Excel, Communication, Teamwork, Recruitment, Payroll, MS Office",
        "experience": [
            ("HR Executive, Sunrise Hotels", "May 2022 - Present",
             "Managed recruitment pipelines, onboarding and payroll data in Excel."),
        ],
        "education": "BBA in Human Resources, Delhi University, 2022",
        "projects": "Employee attrition survey report (Excel).",
    },
    {
        "file": "vikram_joshi.txt",
        "name": "Vikram Joshi",
        "email": "vikram.joshi@example.com",
        "phone": "+91 90040 13579",
        "summary": "Python Python Python SQL SQL Excel Pandas data visualization machine learning deep learning Django REST API.",
        "skills": "Python, SQL, Excel, Pandas, Django, REST API, Machine Learning, Deep Learning, Data Visualization, Python, SQL, Python",
        "experience": [
            ("Trainee, Self-employed", "Jan 2025 - Mar 2025",
             "Learning Python SQL Excel Pandas Django machine learning deep learning."),
        ],
        "education": "Diploma in Computer Applications, 2024",
        "projects": "Python Python SQL projects.",
    },
    {
        "file": "priya_menon.pdf",
        "name": "Priya Menon",
        "email": "priya.menon@example.com",
        "phone": "+91 97400 86420",
        "summary": "Python developer with 2 years of experience in Django, REST APIs and cloud deployment.",
        "skills": "Python, Django, Flask, REST API, SQL, MySQL, Git, Docker, AWS, Linux, HTML, CSS, Problem Solving",
        "experience": [
            ("Python Developer, EduSpark", "Sep 2023 - Present",
             "Built Django REST APIs for a learning platform with 50k users; containerised services with Docker and deployed on AWS."),
            ("Software Intern, Byteline", "Feb 2023 - Aug 2023",
             "Developed Flask microservices and wrote SQL reports."),
        ],
        "education": "B.Tech in Computer Science, Amrita University, 2023",
        "projects": "Online quiz platform (Django); Weather alert bot (Python, REST API).",
    },
]


def resume_lines(c: dict) -> list[tuple[str, str]]:
    """Return resume content as (style, text) pairs: style is 'h1', 'h2' or 'p'."""
    lines = [("h1", c["name"]), ("p", f"Email: {c['email']} | Phone: {c['phone']}"),
             ("h2", "Professional Summary"), ("p", c["summary"]),
             ("h2", "Skills"), ("p", c["skills"]),
             ("h2", "Work Experience")]
    for role, dates, detail in c["experience"]:
        lines += [("p", f"{role} ({dates})"), ("p", f"- {detail}")]
    lines += [("h2", "Education"), ("p", c["education"]),
              ("h2", "Projects"), ("p", c["projects"])]
    return lines


def write_txt(c: dict, path: Path) -> None:
    out = []
    for style, text in resume_lines(c):
        out.append(text.upper() if style == "h2" else text)
        if style != "p":
            out.append("-" * len(text))
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def write_docx(c: dict, path: Path) -> None:
    doc = Document()
    for style, text in resume_lines(c):
        if style == "h1":
            doc.add_heading(text, level=0)
        elif style == "h2":
            doc.add_heading(text, level=1)
        else:
            para = doc.add_paragraph(text)
            para.runs[0].font.size = Pt(11)
    doc.save(path)


def write_pdf(c: dict, path: Path) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(18, 18, 18)
    for style, text in resume_lines(c):
        if style == "h1":
            pdf.set_font("Helvetica", "B", 20)
            pdf.cell(0, 12, text, new_x="LMARGIN", new_y="NEXT")
        elif style == "h2":
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(30, 64, 175)
            pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
        else:
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))


def main() -> None:
    RESUME_DIR.mkdir(exist_ok=True)
    writers = {".txt": write_txt, ".docx": write_docx, ".pdf": write_pdf}
    for c in CANDIDATES:
        path = RESUME_DIR / c["file"]
        writers[path.suffix](c, path)
        print(f"created {path.name}")


if __name__ == "__main__":
    main()
