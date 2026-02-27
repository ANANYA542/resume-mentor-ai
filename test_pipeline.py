from pipeline import resume_pipeline

sample_resume = """
I made my resume in Canva using tables and icons.
I used fancy fonts and multiple colors.
"""

output = resume_pipeline(sample_resume)

print("\n--- Retrieved RAG Rules ---\n")
for r in output["retrieved_rules"]:
    print(f"- {r['text']} (score: {r['score']:.4f})")

print("\n--- AI Suggestions ---\n")
for i, s in enumerate(output["suggestions"], 1):
    print(f"{i}. {s}")