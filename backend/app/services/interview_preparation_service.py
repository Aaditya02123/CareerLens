from sqlalchemy.orm import Session

from app.models.interview_preparation import (
    InterviewPreparationResponse,
    InterviewQuestion,
)
from app.models.resume import StructuredResume
from app.models.resume_analysis import ResumeAnalysis
from app.models.skills import CategorizedSkillResult
from app.repositories.job_repository import JobRepository
from app.repositories.resume_analysis_repository import (
    ResumeAnalysisRepository,
)
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)


TECHNICAL_LIMIT = 10
RESUME_BASED_LIMIT = 10
BEHAVIORAL_LIMIT = 5
JOB_SPECIFIC_LIMIT = 10
TOTAL_LIMIT = 30


def _add_question(
    questions: list[InterviewQuestion],
    seen_questions: set[str],
    question: InterviewQuestion,
) -> None:
    """Add a question only when it has not already been generated."""
    comparison_value = question.question.casefold()

    if comparison_value in seen_questions:
        return

    seen_questions.add(comparison_value)
    questions.append(question)


def _resume_skill_names(analysis: ResumeAnalysis) -> list[str]:
    """Validate and extract categorized skill names."""
    categorized_skills = CategorizedSkillResult.model_validate(
        analysis.categorized_skills
    )

    names: list[str] = []
    seen: set[str] = set()

    for skill in categorized_skills.skills:
        name = skill.name.strip()
        comparison_value = name.casefold()

        if not name or comparison_value in seen:
            continue

        seen.add(comparison_value)
        names.append(name)

    return names


def _generate_technical_questions(
    job_required_skills: list[str],
    questions: list[InterviewQuestion],
    seen_questions: set[str],
) -> None:
    """Generate questions from required job skills."""
    for skill in job_required_skills[:TECHNICAL_LIMIT]:
        if not skill.strip():
            continue

        _add_question(
            questions=questions,
            seen_questions=seen_questions,
            question=InterviewQuestion(
                question=(
                    f"How would you use {skill} to solve a problem "
                    "relevant to this role?"
                ),
                category="technical",
                difficulty="medium",
            ),
        )


def _generate_resume_questions(
    structured_resume: StructuredResume,
    categorized_skill_names: list[str],
    questions: list[InterviewQuestion],
    seen_questions: set[str],
) -> None:
    """Generate questions from information present in the resume."""
    generated_count = 0

    for project in structured_resume.projects:
        if generated_count >= RESUME_BASED_LIMIT:
            return

        _add_question(
            questions=questions,
            seen_questions=seen_questions,
            question=InterviewQuestion(
                question=(
                    f"Can you explain your contribution to the "
                    f"project '{project}'?"
                ),
                category="resume_based",
                difficulty="medium",
            ),
        )
        generated_count += 1

    for experience in structured_resume.experience:
        if generated_count >= RESUME_BASED_LIMIT:
            return

        _add_question(
            questions=questions,
            seen_questions=seen_questions,
            question=InterviewQuestion(
                question=(
                    f"Can you describe your experience with "
                    f"'{experience}'?"
                ),
                category="resume_based",
                difficulty="medium",
            ),
        )
        generated_count += 1

    for certification in structured_resume.certifications:
        if generated_count >= RESUME_BASED_LIMIT:
            return

        _add_question(
            questions=questions,
            seen_questions=seen_questions,
            question=InterviewQuestion(
                question=(
                    f"What did you learn while completing "
                    f"'{certification}'?"
                ),
                category="resume_based",
                difficulty="easy",
            ),
        )
        generated_count += 1

    for skill in categorized_skill_names:
        if generated_count >= RESUME_BASED_LIMIT:
            return

        _add_question(
            questions=questions,
            seen_questions=seen_questions,
            question=InterviewQuestion(
                question=(
                    f"How have you applied {skill} in your "
                    "academic or professional work?"
                ),
                category="resume_based",
                difficulty="medium",
            ),
        )
        generated_count += 1


def _generate_behavioral_questions(
    questions: list[InterviewQuestion],
    seen_questions: set[str],
) -> None:
    """Generate a small fixed behavioral question set."""
    behavioral_questions = [
        "Tell me about yourself.",
        "Describe a challenging problem you solved.",
        "Tell me about a time you had to learn something quickly.",
        (
            "Describe a time you worked with others to complete "
            "a task."
        ),
    ]

    for question_text in behavioral_questions[:BEHAVIORAL_LIMIT]:
        _add_question(
            questions=questions,
            seen_questions=seen_questions,
            question=InterviewQuestion(
                question=question_text,
                category="behavioral",
                difficulty="easy",
            ),
        )


def _generate_job_questions(
    job_responsibilities: list[str],
    job_description: str,
    questions: list[InterviewQuestion],
    seen_questions: set[str],
) -> None:
    """Generate questions from job responsibilities or description."""
    source_items = [
        responsibility
        for responsibility in job_responsibilities
        if responsibility.strip()
    ]

    if not source_items and job_description.strip():
        source_items = [job_description.strip()]

    for item in source_items[:JOB_SPECIFIC_LIMIT]:
        _add_question(
            questions=questions,
            seen_questions=seen_questions,
            question=InterviewQuestion(
                question=(
                    "How would you approach the following responsibility "
                    f"or expectation: {item}"
                ),
                category="job_specific",
                difficulty="medium",
            ),
        )


def build_interview_preparation(
    resume_id: int,
    job_id: int,
    session: Session,
) -> InterviewPreparationResponse:
    """Build deterministic interview preparation for a resume and job."""
    analysis_repository = ResumeAnalysisRepository(session)
    analysis = analysis_repository.get_by_resume_id(resume_id)

    if analysis is None:
        raise ResumeAnalysisNotFoundError(
            "No persisted resume analysis was found."
        )

    job_repository = JobRepository(session)
    job = job_repository.get_by_id(job_id)

    if job is None:
        raise JobNotFoundError("The requested job was not found.")

    structured_resume = StructuredResume.model_validate(
        analysis.structured_resume
    )
    categorized_skill_names = _resume_skill_names(analysis)

    questions: list[InterviewQuestion] = []
    seen_questions: set[str] = set()

    _generate_technical_questions(
        job_required_skills=job.required_skills,
        questions=questions,
        seen_questions=seen_questions,
    )

    _generate_resume_questions(
        structured_resume=structured_resume,
        categorized_skill_names=categorized_skill_names,
        questions=questions,
        seen_questions=seen_questions,
    )

    _generate_behavioral_questions(
        questions=questions,
        seen_questions=seen_questions,
    )

    _generate_job_questions(
        job_responsibilities=job.responsibilities,
        job_description=job.description,
        questions=questions,
        seen_questions=seen_questions,
    )

    return InterviewPreparationResponse(
        resume_id=resume_id,
        job_id=job_id,
        questions=questions[:TOTAL_LIMIT],
    )