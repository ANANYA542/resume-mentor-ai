from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from resume_mentor_ai.core.ats import (
    combine_scores,
    content_score,
    detect_formatting_issues,
    formatting_score,
    keyword_match_score,
)
from resume_mentor_ai.core.models import (
    AnalysisResult,
    BulletRewrite,
    Feedback,
    ParsedResume,
    ResumeSection,
    ScoreBreakdown,
    SkillGap,
)
from resume_mentor_ai.core.text import extract_bullets, extract_skills, split_sections


def parse_resume(resume_text: str) -> ParsedResume:
    sections = [ResumeSection(name=n, content=c) for n, c in split_sections(resume_text)]
    skills = extract_skills(resume_text)
    bullets = extract_bullets(resume_text)
    return ParsedResume(raw_text=resume_text, sections=sections, extracted_skills=skills, bullet_points=bullets)


def _analysis_id(resume_text: str, job_description: str | None) -> str:
    h = hashlib.sha256()
    h.update(resume_text.encode("utf-8", errors="ignore"))
    if job_description:
        h.update(b"\n---JD---\n")
        h.update(job_description.encode("utf-8", errors="ignore"))
    return h.hexdigest()[:16] + "-" + uuid.uuid4().hex[:8]


def analyze(
    *,
    resume_text: str,
    job_description: str | None,
    retrieved_rules: list[dict[str, Any]] | None = None,
) -> AnalysisResult:
    parsed = parse_resume(resume_text)

    issues = detect_formatting_issues(resume_text)
    fmt = formatting_score(issues)
    content = content_score(resume_text)

    ats, matched, missing = keyword_match_score(resume_text, job_description or "")
    overall = combine_scores(fmt, content, ats)

    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []

    if fmt >= 85:
        strengths.append("Resume appears ATS-friendly in basic formatting (no obvious layout blockers found).")
    else:
        weaknesses.extend(issues)
        suggestions.append("Simplify formatting: single-column layout, no tables/text boxes/images, plain text headings.")

    if content >= 65:
        strengths.append("Good use of impact signals (bullets, action verbs, or quantified outcomes).")
    else:
        weaknesses.append("Bullet content is light on measurable impact (numbers, outcomes, scope).")
        suggestions.append("Rewrite bullets to include action + scope + impact (numbers where possible).")

    if job_description and job_description.strip():
        if ats >= 70:
            strengths.append("Strong keyword alignment with the job description.")
        else:
            weaknesses.append("Keyword alignment with the job description is moderate/low.")
            if missing:
                suggestions.append("Add missing job-relevant keywords where truthfully applicable (skills/tools/domain terms).")

    skill_gap = None
    if job_description and job_description.strip():
        skill_gap = SkillGap(matched_skills=matched, missing_skills=missing)

    # Basic bullet rewrites (deterministic). LLM rewrites are added later via AI layer.
    rewrites: list[BulletRewrite] = []
    for b in parsed.bullet_points[:8]:
        rewritten = b
        if not any(ch.isdigit() for ch in b):
            rewritten = b.rstrip(".") + " (add measurable impact: %, $, time saved, scale, or users)."
        if rewritten == b:
            continue
        rewrites.append(BulletRewrite(original=b, rewritten=rewritten))

    aid = _analysis_id(resume_text, job_description)
    now = datetime.now(timezone.utc)

    return AnalysisResult(
        analysis_id=aid,
        created_at=now,
        issues=issues,
        retrieved_rules=retrieved_rules or [],
        score=ScoreBreakdown(overall=overall, formatting=fmt, content=content, ats_match=ats),
        feedback=Feedback(strengths=strengths, weaknesses=weaknesses, suggestions=suggestions),
        skill_gap=skill_gap,
        bullet_rewrites=rewrites,
        resume_summary={
            "sections_detected": [s.name for s in parsed.sections],
            "skills_detected": parsed.extracted_skills,
            "bullets_detected": len(parsed.bullet_points),
        },
    )

