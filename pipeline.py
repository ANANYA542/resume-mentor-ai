from retriever import retrieve_context

def resume_pipeline(resume_text):
    """
    Full RAG pipeline (without LLM for now)
    """
    rules = retrieve_context(resume_text, k=5)
    return {
        "resume": resume_text,
        "retrieved_rules": rules
    }