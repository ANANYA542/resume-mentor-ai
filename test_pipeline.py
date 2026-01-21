from pipeline import resume_pipeline

sample_resume = """
I made my resume in Canva with tables and icons.
I used fancy fonts and colors.
"""

output = resume_pipeline(sample_resume)

print("\nRetrieved context:\n")
for r in output["retrieved_rules"]:
    print("-", r)