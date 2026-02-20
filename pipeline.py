def detect_resume_issues(resume_text):
    text = resume_text.lower()
    issues = []

    if "canva" in text:
        issues.append("Uses Canva formatting")
    if "icon" in text or "image" in text or "graphic" in text:
        issues.append("Uses images or icons")
    if "fancy font" in text or "decorative" in text:
        issues.append("Uses bad fonts")
    if "table" in text:
        issues.append("Uses tables for layout")
    if "png" in text or "jpg" in text:
        issues.append("Wrong file format")

    return issues
from improver import generate_suggestions
def calculate_resume_score(issues):
    base_score = 100
    penalty_per_issue = 12

    score = base_score - (len(issues) * penalty_per_issue)

    if score < 0:
        score = 0

    return score

def resume_pipeline(resume_text):
    # Step 1: Detect problems
    issues = detect_resume_issues(resume_text)
    score = calculate_resume_score(issues)

    # Step 2: Retrieve rules using RAG
    try:
        from retriever import retrieve_context

        retrieved = retrieve_context(resume_text)
    except Exception:
        retrieved = []

    # Step 3: Generate suggestions
    suggestions = generate_suggestions(resume_text, retrieved)

    return {
        "issues": issues,
        "score": score,
        "retrieved_rules": retrieved,
        "suggestions": suggestions
    }