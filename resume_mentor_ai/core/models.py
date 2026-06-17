from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None


class ResumeInput(BaseModel):
    resume_text: Optional[str] = Field(default=None, description="Raw resume text.")
    job_description: Optional[str] = Field(default=None, description="Optional job description text.")
    resume_pdf_path: Optional[str] = Field(
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
    quick_wins: list[str] = []


class SkillGap(BaseModel):
    missing_skills: list[str] = []
    matched_skills: list[str] = []
    match_percentage: float = 0.0


class BulletRewrite(BaseModel):
    original: str
    rewritten: str
    rationale: Optional[str] = None


class AnalysisResult(BaseModel):
    analysis_id: str
    created_at: datetime
    issues: list[str] = []
    retrieved_rules: list[dict[str, Any]] = []
    score: ScoreBreakdown
    feedback: Feedback
    skill_gap: Optional[SkillGap] = None
    bullet_rewrites: list[BulletRewrite] = []
    resume_summary: dict[str, Any] = {}
