from retriever import retrieve_context
from improver import generate_suggestions

def resume_pipeline(resume_text):
    rules = retrieve_context(resume_text, k=5)
    suggestions = generate_suggestions(resume_text, rules)

    return {
        "resume": resume_text,
        "retrieved_rules": rules,
        "suggestions": suggestions
    }