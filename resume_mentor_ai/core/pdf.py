from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def extract_text_from_pdf(pdf_path: str) -> str:
    path = Path(pdf_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")

    reader = PdfReader(str(path))
    pages_text: list[str] = []
    for page in reader.pages:
        txt = page.extract_text() or ""
        txt = txt.replace("\r\n", "\n").replace("\r", "\n").strip()
        if txt:
            pages_text.append(txt)
    return "\n\n".join(pages_text).strip()

