import re

# Simple keyword-based mapping from rules to actionable suggestions.
# This keeps the system fully local (no LLM) and deterministic.

def generate_suggestions(resume_text, rules):
    """
    Maps retrieved rules to concrete, actionable suggestions.

    Parameters:
    - resume_text (str): The original resume text.
    - rules (list): List of dicts like {"text": <rule>, "score": <float>} returned by RAG.

    Returns:
    - suggestions (list[str]): Human-readable improvement actions.
    """

    suggestions = []

    # Normalize resume text for simple checks
    resume_lower = resume_text.lower()

    for rule_obj in rules:
        rule = rule_obj["text"].lower()

        # ATS + formatting rules
        if "images" in rule or "icons" in rule or "graphics" in rule:
            suggestions.append(
                "Remove all images, icons, and graphics. Use plain text so ATS systems can read your resume correctly."
            )

        elif "tables" in rule or "text boxes" in rule:
            suggestions.append(
                "Avoid tables and text boxes. Use a simple single-column layout with normal paragraphs and bullet points."
            )

        elif "simple fonts" in rule or "fonts" in rule:
            suggestions.append(
                "Switch to simple fonts like Arial, Calibri, or Times New Roman and avoid decorative fonts."
            )

        elif "pdf or docx" in rule:
            suggestions.append(
                "Export your resume as a PDF or DOCX file instead of using images or design formats like Canva."
            )

        elif "standard headings" in rule:
            suggestions.append(
                "Use standard section headings such as Experience, Education, Skills, and Projects."
            )

        elif "spacing and alignment" in rule:
            suggestions.append(
                "Ensure consistent spacing and alignment. Avoid uneven margins or misaligned bullet points."
            )

        elif "one page" in rule:
            suggestions.append(
                "Limit your resume to one page if you are a fresher or student."
            )

        elif "bullet points" in rule:
            suggestions.append(
                "Use bullet points instead of long paragraphs to make your resume easier to read."
            )

        # Strong bullet writing rules
        elif "action verbs" in rule:
            suggestions.append(
                "Start each bullet point with a strong action verb such as Built, Designed, Implemented, or Developed."
            )

        elif "quantify" in rule or "numbers" in rule:
            suggestions.append(
                "Add numbers to show impact, e.g., 'Improved performance by 30%' or 'Handled 1000+ users'."
            )

        elif "impact" in rule:
            suggestions.append(
                "Rewrite bullets to show results and impact instead of just listing tasks."
            )

        elif "vague" in rule:
            suggestions.append(
                "Replace vague phrases like 'worked on' with clear, specific actions and outcomes."
            )

        # General resume best practices
        elif "tailor your resume" in rule:
            suggestions.append(
                "Customize your resume keywords and skills based on the specific job description."
            )

        elif "proofread" in rule:
            suggestions.append(
                "Proofread your resume carefully to remove spelling and grammar mistakes."
            )

        else:
            # Fallback for any rule that doesn't match our patterns
            suggestions.append(
                f"Apply this guideline: {rule_obj['text']}"
            )

    # Remove duplicates while preserving order
    unique_suggestions = []
    for s in suggestions:
        if s not in unique_suggestions:
            unique_suggestions.append(s)

    return unique_suggestions