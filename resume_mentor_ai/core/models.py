from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    ok: bool
    data: Any | None = None
    error: str | None = None


class ResumeInput(BaseModel):
    resume_text: str | None = Field(default=None, description="Raw resume text.")
    job_description: str | None = Field(default=None, description="Optional job description text.")
    resume_pdf_path: str | None = Field(
        default=None,
        description="Optional local path to a PDF resume (server-side). Prefer resume_text for API usage.",
    )
    candidate_level: Literal["student", "junior", "mid", "senior"] = "junior"


class ResumeSection(BaseModel):
    name: str
    content: str


class ParsedResume(BaseModel):
    raw_text: str
    sections: list[ResumeSection]
    extracted_skills: list[str] = []
    bullet_points: list[str] = []


class ScoreBreakdown(BaseModel):
    overall: int = Field(ge=0, le=100)
    formatting: int = Field(ge=0, le=100)
    content: int = Field(ge=0, le=100)
    ats_match: int = Field(ge=0, le=100)


class Feedback(BaseModel):
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []


class SkillGap(BaseModel):
    missing_skills: list[str] = []
    matched_skills: list[str] = []


class BulletRewrite(BaseModel):
    original: str
    rewritten: str
    rationale: str | None = None


class AnalysisResult(BaseModel):
    analysis_id: str
    created_at: datetime
    issues: list[str] = []
    retrieved_rules: list[dict[str, Any]] = []
    score: ScoreBreakdown
    feedback: Feedback
    skill_gap: SkillGap | None = None
    bullet_rewrites: list[BulletRewrite] = []
    resume_summary: dict[str, Any] = {}

