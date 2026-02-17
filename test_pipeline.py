from pipeline import resume_pipeline

sample_resume = """
I made my resume in Canva using tables and icons.
I used fancy fonts and colorful layouts.
"""

output = resume_pipeline(sample_resume)

print("\nRetrieved RAG context:\n")
for r in output["retrieved_rules"]:
    print(f"- {r['text']} (score: {r['score']:.4f})")