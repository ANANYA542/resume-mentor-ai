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
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_bullets(text: str, max_bullets: int = 40) -> list[str]:
    bullets: list[str] = []
    for line in normalize_whitespace(text).split("\n"):
        s = line.strip()
        if not s:
            continue
        if re.match(r"^(\-|\*|•|\u2022)\s+", s):
            bullets.append(re.sub(r"^(\-|\*|•|\u2022)\s+", "", s).strip())
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

    # skill-y tokens and abbreviations; intentionally small and extendable
    vocab = {
        "python",
        "java",
        "javascript",
        "typescript",
        "react",
        "node",
        "fastapi",
        "flask",
        "django",
        "sql",
        "postgres",
        "mysql",
        "mongodb",
        "docker",
        "kubernetes",
        "aws",
        "gcp",
        "azure",
        "git",
        "ci/cd",
        "linux",
        "pandas",
        "numpy",
        "scikit-learn",
        "pytorch",
        "tensorflow",
        "nlp",
        "llm",
        "faiss",
        "streamlit",
    }

    def add_from_text(blob: str):
        low = blob.lower()
        for v in vocab:
            if v in low:
                skills.add(v)
        # capture patterns like "C++", "C#", "REST API"
        for m in re.findall(r"\b(c\+\+|c#|rest api|rest|graphql|jwt)\b", low):
            skills.add(m)

    # prioritize skills-like sections
    for name, content in split_sections(t):
        if "skill" in name:
            add_from_text(content)

    add_from_text(t)
    return sorted(skills)

