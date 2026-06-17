from __future__ import annotations

import math
import re
from dataclasses import dataclass


def detect_formatting_issues(resume_text: str) -> list[str]:
    text = resume_text.lower()
    issues: list[str] = []

    if re.search(r"\bcanva\b", text):
        issues.append("Uses Canva formatting")
    if re.search(r"\bicons?\b", text) or re.search(r"\bimages?\b", text) or re.search(r"\bgraphics?\b", text):
        issues.append("Uses images or icons")
    if re.search(r"\btables?\b", text):
        issues.append("Uses tables for layout")
    if re.search(r"\btext box\b", text) or re.search(r"\btextbox\b", text):
        issues.append("Uses text boxes")
    if re.search(r"\bheaders?\b", text) or re.search(r"\bfooters?\b", text):
        issues.append("Important info may be in headers/footers")
    if re.search(r"\bpng\b", text) or re.search(r"\bjpg\b", text):
        issues.append("Mentions image formats (PNG/JPG) instead of PDF/DOCX")

    return issues


def _tokenize(text: str) -> list[str]:
    t = text.lower()
    t = re.sub(r"[^a-z0-9\+\#\/\.\s-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return [w for w in t.split(" ") if len(w) >= 2]


@dataclass(frozen=True)
class KeywordMatchResult:
    score: int
    matched: list[str]
    missing: list[str]
    total_jd_keywords: int


def keyword_match_score(resume_text: str, job_description: str) -> KeywordMatchResult:
    """
    Returns a lightweight keyword-overlap result.
    """
    if not job_description or not job_description.strip():
        return KeywordMatchResult(score=0, matched=[], missing=[], total_jd_keywords=0)

    r = set(_tokenize(resume_text))
    jd_tokens = _tokenize(job_description)

    # emphasize "skills-like" tokens: de-duplicate while preserving signal
    jd = []
    seen = set()
    for w in jd_tokens:
        if w in seen:
            continue
        if w in {"and", "the", "with", "for", "to", "in", "of", "a", "an", "looking", "seeking", "role", "candidate"}:
            continue
        if w.isdigit():
            continue
        seen.add(w)
        jd.append(w)

    if not jd:
        return KeywordMatchResult(score=0, matched=[], missing=[], total_jd_keywords=0)

    matched = [w for w in jd if w in r]
    missing = [w for w in jd if w not in r]

    raw = len(matched) / max(1, len(jd))
    score = int(round(100 * raw))
    return KeywordMatchResult(
        score=score,
        matched=matched[:60],
        missing=missing[:60],
        total_jd_keywords=len(jd),
    )


def formatting_score(issues: list[str]) -> int:
    base = 100
    penalty = 12
    score = base - penalty * len(issues)
    return max(0, min(100, score))


@dataclass(frozen=True)
class ScoreParts:
    formatting: int
    content: int
    ats_match: int
    overall: int


def content_score(resume_text: str) -> int:
    """
    Simple content heuristic: rewards measurable impact and bullet structure.
    """
    t = resume_text
    bullets = len(re.findall(r"(^|\n)\s*(\-|\*|•|\u2022)\s+", t))
    numbers = len(re.findall(r"\b\d+(\.\d+)?%?\b", t))
    action_verbs = len(re.findall(r"\b(built|designed|implemented|improved|led|developed|optimized|deployed)\b", t, re.I))

    # squashed, bounded scoring
    b = 1 - math.exp(-bullets / 8)
    n = 1 - math.exp(-numbers / 6)
    a = 1 - math.exp(-action_verbs / 6)
    score = int(round(100 * (0.45 * b + 0.35 * n + 0.20 * a)))
    return max(0, min(100, score))


def combine_scores(formatting: int, content: int, ats_match: int) -> int:
    overall = int(round(0.35 * formatting + 0.35 * content + 0.30 * ats_match))
    return max(0, min(100, overall))
