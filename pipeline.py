from retriever import retrieve_context

def resume_pipeline(resume_text):
    rules = retrieve_context(resume_text, k=5)

    return {
        "resume": resume_text,
        "retrieved_rules": rules
    }