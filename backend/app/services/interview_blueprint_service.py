from __future__ import annotations

import json
import time
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
from app.services.llm.structured import (
    generate_structured_text,
    parse_and_validate_model,
)
from app.services.llm.observability import (
    GenerationFailureCategory,
    classify_generation_error,
    elapsed_ms,
    generation_context,
    log_generation_event,
    new_correlation_id,
    provider_status_code,
)


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

    def __init__(
        self,
        message: str,
        *,
        failure_category: GenerationFailureCategory = (
            GenerationFailureCategory.UNKNOWN_GENERATION_ERROR
        ),
    ) -> None:
        super().__init__(message)
        self.failure_category = failure_category


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
        "Use only the enum values supplied by the schema. Return integer "
        "weights that total 100 for competencies and rubric criteria. "
        "Return exactly the configured number of questions, with each "
        "question's estimated_response_seconds between 15 and 600. "
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


def _parse_provider_payload_with_timings(
    raw: str,
) -> tuple[InterviewBlueprintGenerationPayload, float, float]:
    try:
        result = parse_and_validate_model(
            raw,
            InterviewBlueprintGenerationPayload,
        )
    except ValidationError as error:
        raise InterviewBlueprintProviderError(
            "The interview blueprint provider returned schema-invalid data.",
            failure_category=GenerationFailureCategory.SCHEMA_VALIDATION_FAILED,
        ) from error
    except (ValueError, TypeError) as error:
        raise InterviewBlueprintProviderError(
            "The interview blueprint provider returned malformed JSON.",
            failure_category=GenerationFailureCategory.MALFORMED_JSON,
        ) from error
    return (
        result.value,
        result.json_parse_ms,
        result.pydantic_validation_ms,
    )


def _parse_provider_payload(raw: str) -> InterviewBlueprintGenerationPayload:
    payload, _, _ = _parse_provider_payload_with_timings(raw)
    return payload


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

    active_provider = provider or get_ollama_generation_provider()
    base_prompt = build_interview_blueprint_prompt(
        config=active_config,
        job=job,
        structured_resume=structured_resume,
        categorized_skills=categorized_skills,
    )
    correlation_id = new_correlation_id()
    operation_started_at = time.perf_counter()
    payload = None
    for attempt_index in range(2):
        attempt = attempt_index + 1
        prompt = base_prompt
        retry_reason = None
        if attempt_index:
            prompt += (
                "\n\nYour previous response was rejected. Return one corrected "
                "JSON object only. Follow the requested schema, configuration, "
                "weight totals, question count, and grounding rules exactly."
            )
            retry_reason = "previous_attempt_rejected"

        attempt_started_at = time.perf_counter()
        provider_wait_ms = None
        json_parse_ms = None
        pydantic_validation_ms = None
        grounding_validation_ms = None
        try:
            with generation_context(
                operation="blueprint",
                correlation_id=correlation_id,
                attempt=attempt,
                provider=active_provider,
                retry_reason=retry_reason,
            ):
                provider_started_at = time.perf_counter()
                raw = generate_structured_text(
                    active_provider,
                    system_prompt=(
                        "You are a careful CareerLens interview blueprint planner. "
                        "Return only the requested grounded JSON object."
                    ),
                    prompt=prompt,
                    response_schema=(
                        InterviewBlueprintGenerationPayload.model_json_schema()
                    ),
                )
                provider_wait_ms = elapsed_ms(provider_started_at)
                candidate, json_parse_ms, pydantic_validation_ms = (
                    _parse_provider_payload_with_timings(raw)
                )
                grounding_started_at = time.perf_counter()
                _validate_grounding(
                    candidate,
                    config=active_config,
                    job=job,
                    structured_resume=structured_resume,
                )
                grounding_validation_ms = elapsed_ms(grounding_started_at)
            payload = candidate
            log_generation_event(
                event="llm_generation",
                success=True,
                provider=active_provider,
                operation="blueprint",
                correlation_id=correlation_id,
                attempt=attempt,
                provider_wait_ms=provider_wait_ms,
                json_parse_ms=json_parse_ms,
                pydantic_validation_ms=pydantic_validation_ms,
                grounding_validation_ms=grounding_validation_ms,
                total_operation_ms=elapsed_ms(operation_started_at),
            )
            break
        except InterviewBlueprintProviderError as error:
            if error.failure_category == GenerationFailureCategory.UNKNOWN_GENERATION_ERROR:
                error.failure_category = (
                    GenerationFailureCategory.GROUNDING_VALIDATION_FAILED
                )
            if attempt_index == 1:
                log_generation_event(
                    event="llm_generation",
                    success=False,
                    provider=active_provider,
                    operation="blueprint",
                    correlation_id=correlation_id,
                    attempt=attempt,
                    failure_category=GenerationFailureCategory.GENERATION_RETRY_EXHAUSTED,
                    root_failure_category=error.failure_category,
                    retry_reason=error.failure_category.value,
                    provider_wait_ms=provider_wait_ms,
                    json_parse_ms=json_parse_ms,
                    pydantic_validation_ms=pydantic_validation_ms,
                    grounding_validation_ms=grounding_validation_ms,
                    total_operation_ms=elapsed_ms(operation_started_at),
                )
                raise
            log_generation_event(
                event="llm_generation_retry",
                success=False,
                provider=active_provider,
                operation="blueprint",
                correlation_id=correlation_id,
                attempt=attempt,
                failure_category=error.failure_category,
                retry_reason=error.failure_category.value,
                provider_wait_ms=provider_wait_ms,
                json_parse_ms=json_parse_ms,
                pydantic_validation_ms=pydantic_validation_ms,
                grounding_validation_ms=grounding_validation_ms,
                total_attempt_ms=elapsed_ms(attempt_started_at),
            )
        except Exception as error:
            log_generation_event(
                event="llm_generation",
                success=False,
                provider=active_provider,
                operation="blueprint",
                correlation_id=correlation_id,
                attempt=attempt,
                failure_category=classify_generation_error(error),
                provider_http_status=provider_status_code(error),
                provider_wait_ms=provider_wait_ms,
                json_parse_ms=json_parse_ms,
                pydantic_validation_ms=pydantic_validation_ms,
                grounding_validation_ms=grounding_validation_ms,
                total_operation_ms=elapsed_ms(operation_started_at),
            )
            raise

    if payload is None:
        raise InterviewBlueprintProviderError(
            "The interview blueprint provider returned invalid structured data."
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
