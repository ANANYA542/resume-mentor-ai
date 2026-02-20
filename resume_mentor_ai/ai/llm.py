from __future__ import annotations

import json
import os
from typing import Any


class LlmError(RuntimeError):
    pass


def _gemini_enabled() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def generate_json(system_prompt: str, user_prompt: str, json_schema_hint: dict[str, Any]) -> dict[str, Any]:
    """
    Best-effort JSON generation.

    - If GEMINI_API_KEY is set, uses google-generativeai.
    - Otherwise raises LlmError so callers can fall back to deterministic logic.
    """
    if not _gemini_enabled():
        raise LlmError("GEMINI_API_KEY not set")

    try:
        import google.generativeai as genai
    except Exception as e:  # pragma: no cover
        raise LlmError(f"Gemini SDK not available: {e}") from e

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = (
        f"{system_prompt.strip()}\n\n"
        "Return ONLY valid JSON with no markdown fences.\n"
        f"JSON schema hint (keys/types): {json.dumps(json_schema_hint, ensure_ascii=False)}\n\n"
        f"USER:\n{user_prompt.strip()}\n"
    )

    try:
        resp = model.generate_content(prompt)
        text = (getattr(resp, "text", None) or "").strip()
        return json.loads(text)
    except Exception as e:  # pragma: no cover
        raise LlmError(f"Failed to generate JSON: {e}") from e

