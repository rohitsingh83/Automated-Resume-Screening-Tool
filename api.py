"""
REST API so other systems (an ATS, a job portal) can use the screener.

Run:   uvicorn api:app --reload
Docs:  http://127.0.0.1:8000/docs  (interactive Swagger UI)

Endpoints
  GET  /health            service status
  GET  /jobs              available job descriptions
  POST /screen/{job_id}   upload resumes, get the ranked list back
"""

from fastapi import FastAPI, File, HTTPException, UploadFile

from src.extractor import SUPPORTED
from src.screener import load_jobs, screen_uploads, to_dataframe

app = FastAPI(title="Automated Resume Screening API", version="1.0.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/jobs")
def jobs() -> list[dict]:
    return [{"id": j["id"], "title": j["title"], "company": j["company"], "must_have": j["must_have"],
             "min_experience": j["min_experience"]} for j in load_jobs().values()]


@app.post("/screen/{job_id}")
async def screen(job_id: str, files: list[UploadFile] = File(...)) -> dict:
    all_jobs = load_jobs()
    if job_id not in all_jobs:
        raise HTTPException(404, f"Unknown job '{job_id}'")
    uploads = []
    for f in files:
        if not any(f.filename.lower().endswith(ext) for ext in SUPPORTED):
            raise HTTPException(400, f"{f.filename}: only PDF, DOCX and TXT are supported")
        uploads.append((f.filename, await f.read()))
    candidates = screen_uploads(all_jobs[job_id], uploads)
    df = to_dataframe(candidates).drop(columns=["Email"])
    return {"job": all_jobs[job_id]["title"], "count": len(df), "results": df.to_dict(orient="records")}
