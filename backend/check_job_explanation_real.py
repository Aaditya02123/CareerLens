from __future__ import annotations

from app.models.match_explaination import MatchEvidence, MatchExplanationResponse
from app.services.job_explanation_generator import JobExplanationGenerator
from app.services.llm.ollama_generator import OllamaGenerationProvider


def make_no_gap_explanation() -> MatchExplanationResponse:
    return MatchExplanationResponse(
        resume_id=5,
        job_id=2,
        hybrid_score=0.92,
        required_skill_score=1.0,
        preferred_skill_score=0.75,
        semantic_score=0.87,
        matched_required_skills=[
            "Python",
            "FastAPI",
            "PostgreSQL",
        ],
        missing_required_skills=[],
        matched_preferred_skills=[
            "Docker",
        ],
        match_level="strong",
        skill_gap_count=0,
        primary_factors=[
            "All required skills matched.",
            "Strong semantic similarity.",
        ],
        evidence=[
            MatchEvidence(
                skill="Python",
                source_type="skill",
                source_title="Technical Skills",
                excerpt="Python",
                strength="direct",
            ),
            MatchEvidence(
                skill="FastAPI",
                source_type="project",
                source_title="CareerLens",
                excerpt="Built the backend using FastAPI REST APIs.",
                strength="direct",
            ),
            MatchEvidence(
                skill="PostgreSQL",
                source_type="project",
                source_title="CareerLens",
                excerpt="Designed PostgreSQL persistence for career data.",
                strength="direct",
            ),
        ],
    )


def make_sql_gap_explanation() -> MatchExplanationResponse:
    return MatchExplanationResponse(
        resume_id=5,
        job_id=2,
        hybrid_score=0.58,
        required_skill_score=0.50,
        preferred_skill_score=0.0,
        semantic_score=0.71,
        matched_required_skills=[
            "Python",
        ],
        missing_required_skills=[
            "SQL",
        ],
        matched_preferred_skills=[],
        match_level="partial",
        skill_gap_count=1,
        primary_factors=[
            "Some required skills are missing.",
            "Resume and job descriptions have strong semantic similarity.",
        ],
        evidence=[
            MatchEvidence(
                skill="Python",
                source_type="skill",
                source_title="Technical Skills",
                excerpt="Python",
                strength="direct",
            ),
        ],
    )


def run_test(
    *,
    test_name: str,
    explanation: MatchExplanationResponse,
) -> None:
    print()
    print("=" * 80)
    print(test_name)
    print("=" * 80)

    provider = OllamaGenerationProvider(
        model="qwen3.5:9b",
        timeout_seconds=120,
    )

    generator = JobExplanationGenerator(provider)

    result = generator.generate(
        explanation=explanation,
        job_title="Backend Developer",
        company="TechCorp",
    )

    print()
    print(result)
    print()


def main() -> None:
    print("CareerLens real Ollama job-explanation validation")
    print("Model: llama3.2:1b")

    run_test(
        test_name="TEST 1 — NO REQUIRED SKILL GAPS",
        explanation=make_no_gap_explanation(),
    )

    run_test(
        test_name="TEST 2 — SQL REQUIRED SKILL GAP",
        explanation=make_sql_gap_explanation(),
    )


if __name__ == "__main__":
    main()