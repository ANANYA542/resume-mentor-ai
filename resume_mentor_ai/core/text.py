from __future__ import annotations

import re


SECTION_HEADERS = [
    "summary",
    "professional summary",
    "objective",
    "experience",
    "work experience",
    "employment",
    "projects",
    "education",
    "skills",
    "technical skills",
    "certifications",
    "awards",
    "publications",
    "volunteering",
    "leadership",
]


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_bullets(text: str, max_bullets: int = 40) -> list[str]:
    bullets: list[str] = []
    for line in normalize_whitespace(text).split("\n"):
        s = line.strip()
        if not s:
            continue
        match = re.match(r"^(?:[-*•\u2022]|\d+[.)])\s+(.+)$", s)
        if match:
            bullets.append(match.group(1).strip())
    return bullets[:max_bullets]


def split_sections(text: str) -> list[tuple[str, str]]:
    """
    Lightweight section splitter based on header-like lines.
    Returns (section_name, section_content) pairs.
    """
    t = normalize_whitespace(text)
    lines = t.split("\n")

    header_re = re.compile(r"^[A-Z][A-Z \-/&]{2,}$")
    known_re = re.compile(r"^(?:" + "|".join(re.escape(h) for h in SECTION_HEADERS) + r")$", re.I)

    sections: list[tuple[str, list[str]]] = []
    current_name = "unknown"
    current: list[str] = []

    def flush():
        nonlocal current, current_name
        content = "\n".join(current).strip()
        sections.append((current_name, content))
        current = []

    for line in lines:
        s = line.strip()
        if not s:
            current.append("")
            continue

        is_header = bool(header_re.match(s)) or bool(known_re.match(s.lower()))
        if is_header and len(s.split()) <= 5:
            if current:
                flush()
            current_name = s.lower()
            continue
        current.append(s)

    flush()
    merged: list[tuple[str, str]] = []
    for name, content in sections:
        if content.strip():
            merged.append((name, content.strip()))
    return merged


def extract_skills(text: str) -> list[str]:
    """
    Heuristic skill extractor:
    - pulls tokens from 'Skills' sections (if present)
    - also collects common tech tokens from the whole resume
    """
    t = normalize_whitespace(text)
    skills: set[str] = set()

    vocab_patterns: dict[str, str] = {
        "python": r"\bpython\b",
        "java": r"\bjava\b",
        "javascript": r"\bjavascript\b",
        "typescript": r"\btypescript\b",
        "react": r"\breact\b",
        "node": r"\bnode\b",
        "fastapi": r"\bfastapi\b",
        "flask": r"\bflask\b",
        "django": r"\bdjango\b",
        "sql": r"\bsql\b",
        "postgresql": r"\bpostgresql\b",
        "postgres": r"\bpostgres\b",
        "mysql": r"\bmysql\b",
        "mongodb": r"\bmongodb\b",
        "docker": r"\bdocker\b",
        "kubernetes": r"\bkubernetes\b",
        "aws": r"\baws\b",
        "gcp": r"\bgcp\b",
        "azure": r"\bazure\b",
        "git": r"\bgit\b",
        "ci/cd": r"\bci/cd\b",
        "linux": r"\blinux\b",
        "pandas": r"\bpandas\b",
        "numpy": r"\bnumpy\b",
        "scikit-learn": r"\bscikit-learn\b",
        "pytorch": r"\bpytorch\b",
        "tensorflow": r"\btensorflow\b",
        "nlp": r"\bnlp\b",
        "llm": r"\bllm\b",
        "faiss": r"\bfaiss\b",
        "streamlit": r"\bstreamlit\b",
    }

    extra_patterns = {
        "c++": r"\bc\+\+\b",
        "c#": r"\bc#\b",
        "rest api": r"\brest api\b",
        "rest": r"\brest\b",
        "graphql": r"\bgraphql\b",
        "jwt": r"\bjwt\b",
    }

    def add_from_text(blob: str):
        low = blob.lower()
        for skill_name, pattern in vocab_patterns.items():
            if re.search(pattern, low):
                skills.add(skill_name)
        for skill_name, pattern in extra_patterns.items():
            if re.search(pattern, low):
                skills.add(skill_name)

    # prioritize skills-like sections
    for name, content in split_sections(t):
        if "skill" in name:
            add_from_text(content)

    add_from_text(t)
    return sorted(skills)
