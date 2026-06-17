"""
Core analysis pipeline.
 
Entry point: ``analyze()`` — accepts raw resume text and an optional
job description, returns a fully-populated AnalysisResult.
"""
 
from __future__ import annotations
 
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Sequence
 
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
 
logger = logging.getLogger(__name__)
 
# ---------------------------------------------------------------------------
# Thresholds – centralised so they are easy to tune.
# ---------------------------------------------------------------------------
_THRESHOLD_FORMATTING_STRONG = 85
_THRESHOLD_CONTENT_STRONG = 65
_THRESHOLD_ATS_STRONG = 65
_MIN_WORD_COUNT = 50
 
# ---------------------------------------------------------------------------
# Weak opener detection for bullet rewrites
# ---------------------------------------------------------------------------
_WEAK_OPENERS = re.compile(
    r"^(worked on|helped with|assisted with|responsible for|tasked with|"
    r"involved in|participated in|contributed to|was part of)",
    re.I,
)
 
_REPLACEMENTS = {
    "worked on": "Developed",
    "helped with": "Contributed to",
    "assisted with": "Supported",
    "responsible for": "Managed",
    "tasked with": "Delivered",
    "involved in": "Participated in building",
    "participated in": "Collaborated on",
    "contributed to": "Built",
    "was part of": "Collaborated to build",
}
 
 
# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
 
def parse_resume(resume_text: str) -> ParsedResume:
    """Parse raw resume text into a structured ParsedResume."""
    sections = [
        ResumeSection(name=name, content=content)
        for name, content in split_sections(resume_text)
    ]
    skills = extract_skills(resume_text)
    bullets = extract_bullets(resume_text)
    words = resume_text.split()
    return ParsedResume(
        raw_text=resume_text,
        sections=sections,
        extracted_skills=skills,
        bullet_points=bullets,
        word_count=len(words),
        char_count=len(resume_text),
    )
 
 
# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------
 
def _make_analysis_id() -> str:
    """Generate a unique analysis ID: ``<8-char uuid>-<8-char uuid>``."""
    return f"{uuid.uuid4().hex[:8]}-{uuid.uuid4().hex[:8]}"
 
 
# ---------------------------------------------------------------------------
# Bullet rewriting
# ---------------------------------------------------------------------------
 
def _rewrite_bullet(bullet: str) -> BulletRewrite | None:
    """
    Apply deterministic improvements to a single bullet point.
 
    Returns None if no improvement can be made (bullet is already strong).
    """
    original = bullet.strip()
    if not original:
        return None
 
    rewritten = original
    rationale_parts: list[str] = []
    impact_added = False
 
    # Rule 1: Replace weak openers.
    m = _WEAK_OPENERS.match(rewritten)
    if m:
        weak = m.group(0)
        strong = _REPLACEMENTS.get(weak.lower(), "Led")
        rewritten = strong + " " + rewritten[len(weak):].lstrip()
        rationale_parts.append(f"Replaced weak opener '{weak}' with stronger action verb.")
 
    # Rule 2: Flag bullets missing quantified impact.
    has_number = bool(re.search(r"\b\d+", rewritten))
    if not has_number:
        rewritten = rewritten.rstrip(".") + " (quantify: add %, $, time saved, users, or scale)."
        rationale_parts.append("Added prompt to quantify impact.")
        impact_added = True
 
    if rewritten == original:
        return None  # Nothing improved – don't emit a no-op rewrite.
 
    return BulletRewrite(
        original=original,
        rewritten=rewritten,
        rationale=" ".join(rationale_parts) if rationale_parts else None,
        impact_added=impact_added,
    )
 
 
# ---------------------------------------------------------------------------
# Quick wins
# ---------------------------------------------------------------------------
 
def _quick_wins(
    issues: list[str],
    missing_skills: list[str],
    bullets: list[str],
    fmt: int,
    content: int,
) -> list[str]:
    """Generate a short list of the highest-impact, lowest-effort actions."""
    wins: list[str] = []
 
    if issues:
        wins.append(
            f"Fix {len(issues)} formatting issue(s) first — these can cause automatic ATS rejection."
        )
 
    no_number_count = sum(1 for b in bullets if not re.search(r"\b\d+", b))
    if no_number_count > 0:
        wins.append(
            f"Add numbers/metrics to {no_number_count} bullet(s) "
            f"(e.g., 'Improved load time by 40%', 'Served 10k daily users')."
        )
 
    if missing_skills[:5]:
        wins.append(
            "Add these keywords from the JD (if truthfully applicable): "
            + ", ".join(missing_skills[:5])
            + "."
        )
 
    if content < 40:
        wins.append(
            "Your resume has very few bullet points or action verbs — "
            "add 6–10 achievement-focused bullets using the STAR format."
        )
 
    return wins[:4]
 
 
# ---------------------------------------------------------------------------
# Main analysis function
# ---------------------------------------------------------------------------
 
def analyze(
    *,
    resume_text: str,
    job_description: str | None,
    retrieved_rules: Sequence[dict[str, Any]] | None = None,
    candidate_level: str = "junior",
) -> AnalysisResult:
    """
    Run the full resume analysis pipeline.
 
    Parameters
    ----------
    resume_text:
        Raw resume text (required).
    job_description:
        Optional job description to compare against.
    retrieved_rules:
        Optional list of RAG-retrieved rules to include in the result.
    candidate_level:
        One of 'student', 'junior', 'mid', 'senior'.
 
    Returns
    -------
    AnalysisResult
 
    Raises
    ------
    ValueError
        If resume_text is empty or too short to be a real resume.
    """
    # --- Input validation ---------------------------------------------------
    if not resume_text or not resume_text.strip():
        raise ValueError("resume_text must not be empty.")
    word_count = len(resume_text.split())
    if word_count < _MIN_WORD_COUNT:
        raise ValueError(
            f"resume_text appears too short ({word_count} words). "
            f"Minimum is {_MIN_WORD_COUNT} words."
        )
 
    t0 = time.perf_counter()
    aid = _make_analysis_id()
    logger.info("analyze() start | id=%s | words=%d | level=%s", aid, word_count, candidate_level)
 
    # --- Parse --------------------------------------------------------------
    parsed = parse_resume(resume_text)
 
    # --- Score --------------------------------------------------------------
    issues = detect_formatting_issues(resume_text)
    fmt = formatting_score(issues)
    cont = content_score(resume_text)
    kw_result = keyword_match_score(resume_text, job_description or "")
    ats = kw_result.score
    overall = combine_scores(fmt, cont, ats)
 
    # --- Feedback -----------------------------------------------------------
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []
 
    # Formatting feedback.
    if fmt >= _THRESHOLD_FORMATTING_STRONG:
        strengths.append("Clean ATS-friendly formatting — no layout blockers detected.")
    else:
        weaknesses.extend(issues)
        suggestions.append(
            "Use a single-column plain-text layout. Remove tables, text boxes, "
            "images, and Canva exports."
        )
 
    # Content feedback.
    if cont >= _THRESHOLD_CONTENT_STRONG:
        strengths.append("Good use of action verbs and quantified achievements.")
    else:
        weaknesses.append("Bullets lack measurable impact (numbers, outcomes, scope).")
        suggestions.append(
            "Rewrite bullets using the STAR format: "
            "Situation → Task → Action → Result. Include %, $, time, or scale."
        )
 
    # Word-count check (level-aware).
    min_words = {"student": 150, "junior": 200, "mid": 250, "senior": 300}.get(
        candidate_level, 200
    )
    if word_count < min_words:
        weaknesses.append(
            f"Resume may be too short for a {candidate_level}-level candidate "
            f"({word_count} words; aim for {min_words}+)."
        )
 
    # ATS / JD feedback.
    if job_description and job_description.strip():
        if ats >= _THRESHOLD_ATS_STRONG:
            strengths.append(
                f"Strong keyword alignment with job description "
                f"({ats}% of JD keywords matched)."
            )
        else:
            weaknesses.append(
                f"Keyword alignment with JD is low ({ats}% matched; "
                f"{len(kw_result.missing)} keywords missing)."
            )
            if kw_result.missing:
                suggestions.append(
                    "Add missing JD keywords where truthfully applicable: "
                    + ", ".join(kw_result.missing[:10])
                    + ("…" if len(kw_result.missing) > 10 else ".")
                )
 
    # Incorporate retrieved RAG rules as additional suggestions.
    rules = list(retrieved_rules or [])
    if rules:
        for rule in rules[:5]:
            rule_text = rule.get("text", "")
            if rule_text and rule_text not in suggestions:
                suggestions.append(rule_text)
 
    # --- Skill gap ----------------------------------------------------------
    skill_gap: SkillGap | None = None
    if job_description and job_description.strip():
        match_pct = round(
            100 * len(kw_result.matched) / max(1, kw_result.total_jd_keywords), 1
        )
        skill_gap = SkillGap(
            matched_skills=kw_result.matched,
            missing_skills=kw_result.missing,
            match_percentage=match_pct,
        )
 
    # --- Bullet rewrites ----------------------------------------------------
    rewrites: list[BulletRewrite] = []
    for bullet in parsed.bullet_points[:10]:
        rw = _rewrite_bullet(bullet)
        if rw is not None:
            rewrites.append(rw)
 
    # --- Quick wins ---------------------------------------------------------
    qw = _quick_wins(issues, kw_result.missing, parsed.bullet_points, fmt, cont)
 
    # --- Assemble result ----------------------------------------------------
    elapsed = time.perf_counter() - t0
    logger.info(
        "analyze() done | id=%s | overall=%d | elapsed=%.3fs",
        aid, overall, elapsed,
    )
 
    visible_sections = [
        s.name for s in parsed.sections
        if s.name not in ("header", "unknown")
    ] or ["(no sections detected)"]
 
    return AnalysisResult(
        analysis_id=aid,
        created_at=datetime.now(timezone.utc),
        issues=issues,
        retrieved_rules=rules,
        score=ScoreBreakdown(
            overall=overall,
            formatting=fmt,
            content=cont,
            ats_match=ats,
        ),
        feedback=Feedback(
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            quick_wins=qw,
        ),
        skill_gap=skill_gap,
        bullet_rewrites=rewrites,
        resume_summary={
            "word_count": word_count,
            "sections_detected": visible_sections,
            "skills_detected": parsed.extracted_skills,
            "bullets_detected": len(parsed.bullet_points),
            "candidate_level": candidate_level,
            "analysis_time_ms": round(elapsed * 1000),
        },
    )