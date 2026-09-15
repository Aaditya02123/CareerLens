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

PRIORITY_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
}

CATEGORY_ORDER = {
    "technical": 0,
    "job_specific": 1,
    "resume_based": 2,
    "behavioral": 3,
}


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


def _missing_required_skill(
    skill: str,
    resume_skill_keys: set[str],
) -> bool:
    """Determine whether a required skill is absent from the resume."""
    return skill.strip().casefold() not in resume_skill_keys


def _matching_missing_skill(
    text: str,
    missing_required_skills: list[str],
) -> str | None:
    """Find a missing required skill explicitly referenced in text."""
    normalized_text = text.casefold()

    for skill in missing_required_skills:
        if skill.casefold() in normalized_text:
            return skill

    return None


def _generate_technical_questions(
    job_required_skills: list[str],
    resume_skill_names: list[str],
    questions: list[InterviewQuestion],
    seen_questions: set[str],
) -> None:
    """Generate questions from required job skills."""
    resume_skill_keys = {
        skill.casefold()
        for skill in resume_skill_names
    }

    unique_skills: list[str] = []
    seen_skills: set[str] = set()

    for skill in job_required_skills:
        cleaned_skill = skill.strip()
        comparison_value = cleaned_skill.casefold()

        if not cleaned_skill or comparison_value in seen_skills:
            continue

        seen_skills.add(comparison_value)
        unique_skills.append(cleaned_skill)

    for skill in unique_skills[:TECHNICAL_LIMIT]:
        is_missing = _missing_required_skill(
            skill=skill,
            resume_skill_keys=resume_skill_keys,
        )

        if is_missing:
            priority = "high"
            reason = (
                f"{skill} is listed as a required skill for this job "
                "but is not present in the resume."
            )
        else:
            priority = "medium"
            reason = (
                f"{skill} is listed as a required skill for this job "
                "and appears in the resume."
            )

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
                priority=priority,
                reason=reason,
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
                priority="medium",
                reason="This question is based on a project listed "
                "in the resume.",
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
                priority="medium",
                reason="This question is based on experience listed "
                "in the resume.",
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
                priority="medium",
                reason="This question is based on a certification "
                "listed in the resume.",
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
                priority="medium",
                reason=f"{skill} appears in the candidate's resume.",
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
                priority="low",
                reason=(
                    "This question evaluates a general behavioral "
                    "competency relevant to interviews."
                ),
            ),
        )


def _generate_job_questions(
    job_responsibilities: list[str],
    job_description: str,
    missing_required_skills: list[str],
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
        related_missing_skill = _matching_missing_skill(
            text=item,
            missing_required_skills=missing_required_skills,
        )

        if related_missing_skill is not None:
            priority = "high"
            reason = (
                f"This job responsibility is directly related to the "
                f"missing required skill {related_missing_skill}."
            )
        else:
            priority = "medium"
            reason = (
                "This question is based on a responsibility or "
                "expectation listed for the job."
            )

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
                priority=priority,
                reason=reason,
            ),
        )


def _sort_questions(
    questions: list[InterviewQuestion],
) -> list[InterviewQuestion]:
    """Sort by priority, category, and original stable order."""
    return sorted(
        questions,
        key=lambda question: (
            PRIORITY_ORDER[question.priority],
            CATEGORY_ORDER[question.category],
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
        resume_skill_names=categorized_skill_names,
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

    resume_skill_keys = {
        skill.casefold()
        for skill in categorized_skill_names
    }
    missing_required_skills = [
        skill
        for skill in job.required_skills
        if skill.strip()
        and skill.casefold() not in resume_skill_keys
    ]

    _generate_job_questions(
        job_responsibilities=job.responsibilities,
        job_description=job.description,
        missing_required_skills=missing_required_skills,
        questions=questions,
        seen_questions=seen_questions,
    )

    sorted_questions = _sort_questions(questions)

    return InterviewPreparationResponse(
        resume_id=resume_id,
        job_id=job_id,
        questions=sorted_questions[:TOTAL_LIMIT],
    )