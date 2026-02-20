from __future__ import annotations

from fastapi import FastAPI

from resume_mentor_ai.core.models import ApiResponse, ResumeInput
from resume_mentor_ai.core.pdf import extract_text_from_pdf
from resume_mentor_ai.services.analyzer import analyze
from resume_mentor_ai.services.storage import Storage

def _safe_retrieve(resume_text: str) -> list[dict]:
    # Optional dependency: this can be slow / fail if torch/faiss aren't healthy.
    try:
        if len(resume_text) > 50_000:
            return []
        from retriever import retrieve_context  # type: ignore

        return retrieve_context(resume_text, k=8)
    except Exception:
        return []


app = FastAPI(title="Resume Mentor AI", version="0.1.0")


@app.get("/health", response_model=ApiResponse)
def health() -> ApiResponse:
    return ApiResponse(ok=True, data={"status": "up"})


@app.post("/analyze", response_model=ApiResponse)
def analyze_resume(payload: ResumeInput) -> ApiResponse:
    resume_text = payload.resume_text or ""
    if payload.resume_pdf_path and not resume_text.strip():
        resume_text = extract_text_from_pdf(payload.resume_pdf_path)

    if not resume_text.strip():
        return ApiResponse(ok=False, error="Provide resume_text or resume_pdf_path")

    # Do retrieval only when requested by having no JD (so latency stays low).
    # This keeps API responsive even if local embedding stack is slow.
    retrieved = []
    if not (payload.job_description and payload.job_description.strip()):
        retrieved = _safe_retrieve(resume_text)

    result = analyze(resume_text=resume_text, job_description=payload.job_description, retrieved_rules=retrieved)
    data = result.model_dump(mode="json")
    Storage.default().save_analysis(result.analysis_id, data)
    return ApiResponse(ok=True, data=data)


@app.get("/versions", response_model=ApiResponse)
def list_versions(limit: int = 20) -> ApiResponse:
    return ApiResponse(ok=True, data=Storage.default().list_analyses(limit=limit))


@app.get("/versions/{analysis_id}", response_model=ApiResponse)
def get_version(analysis_id: str) -> ApiResponse:
    data = Storage.default().load_analysis(analysis_id)
    if data is None:
        return ApiResponse(ok=False, error="Not found")
    return ApiResponse(ok=True, data=data)

