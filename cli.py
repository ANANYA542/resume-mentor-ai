from pipeline import resume_pipeline

print("==== Resume Mentor AI (RAG Engine) ====\n")
print("Paste your resume text below. Type 'END' on a new line to finish:\n")

lines = []
while True:
    line = input()
    if line.strip() == "END":
        break
    lines.append(line)

resume_text = "\n".join(lines)

output = resume_pipeline(resume_text)

print("\n--- AI Retrieved Key Resume Rules ---\n")
for i, rule in enumerate(output["retrieved_rules"], 1):
    print(f"{i}. {rule['text']} (score: {rule['score']:.4f})")