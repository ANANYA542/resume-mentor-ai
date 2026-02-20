import argparse
from pathlib import Path

from pipeline import resume_pipeline

try:
    from resume_mentor_ai.core.pdf import extract_text_from_pdf
    from resume_mentor_ai.services.analyzer import analyze
except Exception:
    extract_text_from_pdf = None
    analyze = None

parser = argparse.ArgumentParser(description="Resume Mentor AI")
parser.add_argument("--pdf", type=str, help="Path to resume PDF (local)")
parser.add_argument("--jd", type=str, help="Path to job description text file (local)")
parser.add_argument("--legacy", action="store_true", help="Run legacy pipeline (rules + suggestions)")
args = parser.parse_args()

job_description = None
if args.jd:
    job_description = Path(args.jd).expanduser().read_text(encoding="utf-8", errors="ignore")

resume_text = None
if args.pdf and extract_text_from_pdf is not None:
    resume_text = extract_text_from_pdf(args.pdf)

if resume_text is None:
    print("==== Resume Mentor AI ====\n")
    print("Paste your resume text below. Type 'END' on a new line to finish:\n")
    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)
    resume_text = "\n".join(lines)

if args.legacy or analyze is None:
    output = resume_pipeline(resume_text)
    print("\n--- Detected Resume Issues ---\n")
    if output["issues"]:
        for i, issue in enumerate(output["issues"], 1):
            print(f"{i}. {issue}")
    else:
        print("No major issues detected.")

    if "score" in output:
        print(f"\n--- Score ---\n{output['score']}/100")

    print("\n--- Retrieved Resume Rules ---\n")
    for i, rule in enumerate(output["retrieved_rules"], 1):
        print(f"{i}. {rule['text']} (score: {rule['score']:.4f})")

    print("\n--- Suggestions ---\n")
    for i, suggestion in enumerate(output["suggestions"], 1):
        print(f"{i}. {suggestion}")
else:
    result = analyze(resume_text=resume_text, job_description=job_description, retrieved_rules=[])
    print("\n--- Score ---\n")
    print(result.score.model_dump())
    print("\n--- Strengths ---\n")
    for s in result.feedback.strengths:
        print(f"- {s}")
    print("\n--- Weaknesses ---\n")
    for w in result.feedback.weaknesses:
        print(f"- {w}")
    print("\n--- Suggestions ---\n")
    for s in result.feedback.suggestions:
        print(f"- {s}")
    if result.skill_gap:
        print("\n--- Skill Gap ---\n")
        print("Matched:", ", ".join(result.skill_gap.matched_skills[:20]))
        print("Missing:", ", ".join(result.skill_gap.missing_skills[:20]))