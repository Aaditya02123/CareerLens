from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.interview_blueprint import (
    BlueprintCompetencyDraft,
    BlueprintQuestionDraft,
    BlueprintRubricCriterionDraft,
    InterviewBlueprintConfig,
    InterviewBlueprintGenerationPayload,
    InterviewBlueprintResponse,
)
from app.models.resume import StructuredResume
from app.models.skills import CategorizedSkillResult
from app.repositories.interview_blueprint_repository import (
    InterviewBlueprintRepository,
)
from app.repositories.job_repository import JobRepository
from app.repositories.resume_analysis_repository import (
    ResumeAnalysisRepository,
)
from app.repositories.resume_repository import ResumeRepository
from app.services.llm.generator import LLMGenerationProvider
from app.services.llm.ollama_generator import get_ollama_generation_provider


class BlueprintResumeNotFoundError(LookupError):
    """Raised when the selected resume does not exist."""


class BlueprintJobNotFoundError(LookupError):
    """Raised when the selected job does not exist."""


class BlueprintResumeAnalysisNotFoundError(LookupError):
    """Raised when the resume has no persisted analysis."""


class BlueprintJobDescriptionError(ValueError):
    """Raised when a job lacks usable description context."""


class InterviewBlueprintNotFoundError(LookupError):
    """Raised when a persisted blueprint does not exist."""


class InterviewBlueprintProviderError(RuntimeError):
    """Raised when structured blueprint generation cannot be trusted."""


def build_interview_blueprint_prompt(
    *,
    config: InterviewBlueprintConfig,
    job: Any,
    structured_resume: StructuredResume,
    categorized_skills: CategorizedSkillResult,
) -> str:
    """Build a grounded JSON-only prompt for the provider."""
    context = {
        "configuration": config.model_dump(mode="json"),
        "job": {
            "title": job.title,
            "description": job.description,
            "responsibilities": job.responsibilities,
            "required_skills": job.required_skills,
            "preferred_skills": job.preferred_skills,
        },
        "structured_resume": structured_resume.model_dump(mode="json"),
        "categorized_skills": categorized_skills.model_dump(mode="json"),
    }

    return (
        "Create an interview blueprint as valid JSON only. Do not add "
        "Markdown or commentary. Ground every candidate claim in the "
        "supplied structured resume; distinguish resume evidence, job "
        "requirements, and general technical knowledge. Never invent a "
        "project, contribution, skill, qualification, or achievement. "
        "Use the exact requested configuration. Do not generate candidate "
        "scores or hiring predictions. Competency and rubric weights must "
        "each total 100. The question plan must fit the configured duration. "
        "Return these top-level fields: target_role, interview_type, "
        "difficulty, duration_minutes, question_count, competencies, "
        "questions, rubric. Each question must include a stable question_id, "
        "category, difficulty, target_competency, assessment_objective, "
        "relevance_reason, supporting_job_requirement, "
        "supporting_resume_evidence, expected_answer_topics, "
        "rubric_criteria, estimated_response_seconds, and "
        "follow_up_allowed.\n\nContext:\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
    )


def _parse_provider_payload(raw: str) -> InterviewBlueprintGenerationPayload:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = (
            cleaned.removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )

    try:
        return InterviewBlueprintGenerationPayload.model_validate_json(cleaned)
    except (ValidationError, ValueError, TypeError) as error:
        raise InterviewBlueprintProviderError(
            "The interview blueprint provider returned invalid structured data."
        ) from error


def _flatten_values(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_flatten_values(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_flatten_values(item) for item in value)
    return str(value)


def _validate_grounding(
    payload: InterviewBlueprintGenerationPayload,
    *,
    config: InterviewBlueprintConfig,
    job: Any,
    structured_resume: StructuredResume,
) -> None:
    if payload.interview_type != config.interview_type:
        raise InterviewBlueprintProviderError(
            "The provider did not honor the requested interview type."
        )
    if payload.difficulty != config.difficulty:
        raise InterviewBlueprintProviderError(
            "The provider did not honor the requested difficulty."
        )
    if payload.duration_minutes != config.duration_minutes:
        raise InterviewBlueprintProviderError(
            "The provider did not honor the requested duration."
        )
    if payload.question_count != config.question_count:
        raise InterviewBlueprintProviderError(
            "The provider did not honor the requested question count."
        )
    if len(payload.questions) != config.question_count:
        raise InterviewBlueprintProviderError(
            "The provider returned an unexpected number of questions."
        )

    competency_names = {
        item.name.strip().casefold() for item in payload.competencies
    }
    if sum(item.weight_percent for item in payload.competencies) != 100:
        raise InterviewBlueprintProviderError(
            "Competency weights must total 100."
        )
    if sum(item.weight_percent for item in payload.rubric) != 100:
        raise InterviewBlueprintProviderError("Rubric weights must total 100.")

    if config.focus_competencies:
        requested = {
            item.strip().casefold() for item in config.focus_competencies
        }
        if not requested.issubset(competency_names):
            raise InterviewBlueprintProviderError(
                "The provider omitted a requested focus competency."
            )

    question_ids = [item.question_id for item in payload.questions]
    if len(question_ids) != len(set(question_ids)):
        raise InterviewBlueprintProviderError(
            "Question IDs must be unique within a blueprint."
        )

    criterion_ids = {item.criterion_id for item in payload.rubric}
    resume_text = _flatten_values(
        structured_resume.model_dump(mode="json")
    ).casefold()
    job_text = _flatten_values(
        {
            "title": job.title,
            "description": job.description,
            "responsibilities": job.responsibilities,
            "required_skills": job.required_skills,
            "preferred_skills": job.preferred_skills,
        }
    ).casefold()

    total_seconds = 0
    for question in payload.questions:
        if question.target_competency.casefold() not in competency_names:
            raise InterviewBlueprintProviderError(
                "Every question must target a declared competency."
            )
        if any(item not in criterion_ids for item in question.rubric_criteria):
            raise InterviewBlueprintProviderError(
                "Questions may reference only declared rubric criteria."
            )
        total_seconds += question.estimated_response_seconds

        if question.supporting_resume_evidence:
            if question.supporting_resume_evidence.casefold() not in resume_text:
                raise InterviewBlueprintProviderError(
                    "A question contains unsupported resume evidence."
                )
        if question.supporting_job_requirement:
            if question.supporting_job_requirement.casefold() not in job_text:
                raise InterviewBlueprintProviderError(
                    "A question contains an unsupported job requirement."
                )

    if total_seconds > config.duration_minutes * 60:
        raise InterviewBlueprintProviderError(
            "The question plan exceeds the configured interview duration."
        )


def generate_interview_blueprint(
    *,
    resume_id: int,
    job_id: int,
    session: Session,
    config: InterviewBlueprintConfig | None = None,
    provider: LLMGenerationProvider | None = None,
) -> InterviewBlueprintResponse:
    """Generate, validate, persist, and return one interview blueprint."""
    active_config = config or InterviewBlueprintConfig()

    resume = ResumeRepository(session).get_by_id(resume_id)
    if resume is None:
        raise BlueprintResumeNotFoundError(
            "The requested resume was not found."
        )

    job = JobRepository(session).get_by_id(job_id)
    if job is None:
        raise BlueprintJobNotFoundError("The requested job was not found.")
    if not job.description or not job.description.strip():
        raise BlueprintJobDescriptionError(
            "The selected job has no usable description."
        )

    analysis = ResumeAnalysisRepository(session).get_by_resume_id(resume_id)
    if analysis is None:
        raise BlueprintResumeAnalysisNotFoundError(
            "No persisted resume analysis was found."
        )

    structured_resume = StructuredResume.model_validate(
        analysis.structured_resume
    )
    categorized_skills = CategorizedSkillResult.model_validate(
        analysis.categorized_skills
    )

    raw = (provider or get_ollama_generation_provider()).generate(
        system_prompt=(
            "You are a careful CareerLens interview blueprint planner. "
            "Return only the requested grounded JSON object."
        ),
        prompt=build_interview_blueprint_prompt(
            config=active_config,
            job=job,
            structured_resume=structured_resume,
            categorized_skills=categorized_skills,
        ),
    )
    payload = _parse_provider_payload(raw)
    _validate_grounding(
        payload,
        config=active_config,
        job=job,
        structured_resume=structured_resume,
    )

    repository = InterviewBlueprintRepository(session)
    blueprint = repository.create(
        resume_id=resume_id,
        job_id=job_id,
        target_role=payload.target_role,
        interview_type=payload.interview_type,
        difficulty=payload.difficulty,
        duration_minutes=payload.duration_minutes,
        question_count=payload.question_count,
        competencies=payload.competencies,
        questions=payload.questions,
        rubric=payload.rubric,
    )
    return InterviewBlueprintResponse.model_validate(blueprint)


def get_interview_blueprint(
    blueprint_id: int,
    session: Session,
) -> InterviewBlueprintResponse:
    blueprint = InterviewBlueprintRepository(session).get_by_id(blueprint_id)
    if blueprint is None:
        raise InterviewBlueprintNotFoundError(
            "The requested interview blueprint was not found."
        )
    return InterviewBlueprintResponse.model_validate(blueprint)


def list_interview_blueprints(
    resume_id: int,
    session: Session,
    *,
    offset: int = 0,
    limit: int = 50,
    job_id: int | None = None,
) -> list[InterviewBlueprintResponse]:
    if offset < 0 or limit < 1 or limit > 100:
        raise ValueError("offset must be non-negative and limit must be 1-100.")
    if ResumeRepository(session).get_by_id(resume_id) is None:
        raise BlueprintResumeNotFoundError(
            "The requested resume was not found."
        )
    return [
        InterviewBlueprintResponse.model_validate(item)
        for item in InterviewBlueprintRepository(session).list_by_resume_id(
            resume_id,
            offset=offset,
            limit=limit,
            job_id=job_id,
        )
    ]


def delete_interview_blueprint(blueprint_id: int, session: Session) -> None:
    repository = InterviewBlueprintRepository(session)
    if repository.get_by_id(blueprint_id) is None:
        raise InterviewBlueprintNotFoundError(
            "The requested interview blueprint was not found."
        )
    repository.delete_by_id(blueprint_id)
