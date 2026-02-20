from resume_mentor_ai.services.analyzer import analyze


def test_analyze_smoke():
    result = analyze(
        resume_text="Built a FastAPI service and improved latency by 30%.",
        job_description="FastAPI Python latency optimization",
        retrieved_rules=[],
    )

    assert result.score.overall >= 0
    assert result.score.overall <= 100
    assert result.feedback.suggestions
    assert result.skill_gap is not None

