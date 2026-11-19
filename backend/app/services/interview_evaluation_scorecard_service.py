from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.interview_scorecard import (
    AnswerEvaluationResponse,
    CompetencyScoreResponse,
    InterviewAnswerEvaluation,
    InterviewScorecardResponse,
    ProviderAnswerEvaluation,
    ScorecardStatus,
)
from app.models.resume import StructuredResume
from app.models.skills import CategorizedSkillResult
from app.repositories.interview_blueprint_repository import (
    InterviewBlueprintRepository,
)
from app.repositories.interview_evaluation_repository import (
    InterviewEvaluationRepository,
)
from app.repositories.interview_execution_repository import (
    InterviewExecutionRepository,
)
from app.repositories.job_repository import JobRepository
from app.repositories.resume_analysis_repository import (
    ResumeAnalysisRepository,
)
from app.services.interview_execution_service import (
    InterviewExecutionSessionNotFoundError,
)
from app.services.llm.generator import LLMGenerationProvider
from app.services.llm.ollama_generator import get_ollama_generation_provider
from app.services.llm.structured import (
    generate_structured_text,
    parse_json_object,
)


class InterviewAnswerNotFoundForEvaluationError(LookupError):
    """Raised when an answer is missing from the requested session."""


class InterviewResumeAnalysisNotFoundError(LookupError):
    """Raised when the blueprint resume has no persisted analysis."""


class InterviewJobNotFoundError(LookupError):
    """Raised when the blueprint's job no longer exists."""


class InterviewEvaluationError(ValueError):
    """Raised when an answer cannot be evaluated safely."""


class InterviewEvaluationProviderError(RuntimeError):
    """Raised when provider output is malformed or unusable."""


def build_answer_evaluation_prompt(
    *,
    question: Any,
    answer: Any,
    parent_question: Any | None,
    parent_answer: Any | None,
    competency: Any,
    criteria: list[Any],
    job: Any,
    structured_resume: StructuredResume,
    categorized_skills: CategorizedSkillResult,
) -> str:
    context = {
        "question": {
            "id": question.id,
            "text": question.question,
            "category": question.question_category,
            "difficulty": question.difficulty,
        },
        "answer": answer.answer,
        "parent_context": (
            {
                "question": parent_question.question,
                "answer": parent_answer.answer if parent_answer else None,
            }
            if parent_question is not None
            else None
        ),
        "competency": {
            "name": competency.name,
            "description": competency.description,
            "weight_percent": competency.weight_percent,
        },
        "rubric_criteria": [
            {
                "criterion_id": criterion.criterion_id,
                "name": criterion.name,
                "description": criterion.description,
                "weight_percent": criterion.weight_percent,
                "scale_min": criterion.scale_min,
                "scale_max": criterion.scale_max,
            }
            for criterion in criteria
        ],
        "job": {
            "title": job.title,
            "description": job.description,
            "required_skills": job.required_skills,
            "preferred_skills": job.preferred_skills,
        },
        "structured_resume": structured_resume.model_dump(mode="json"),
        "categorized_skills": categorized_skills.model_dump(mode="json"),
    }
    return (
        "Evaluate this interview answer using only the supplied context and "
        "the listed rubric criteria. Return JSON only with answer_id, "
        "question_id, competency_reference, criterion_evaluations, strengths, "
        "improvement_areas, actionable_feedback, and evaluation_status. Each "
        "criterion must be evaluated exactly once with a score from 0 to 5, "
        "a concise justification, answer excerpts only, and one improvement "
        "suggestion. Set evaluation_status to exactly 'complete'. Do not add "
        "fields outside the requested schema. Do not expose chain-of-thought. "
        "Do not infer personality, "
        "honesty, emotion, intelligence, employability, or hiring outcomes. "
        "Do not invent experience, projects, technologies, achievements, or "
        "qualifications. If evidence is insufficient, say so explicitly.\n\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
    )


def _parse_provider_output(raw: str) -> ProviderAnswerEvaluation:
    try:
        return ProviderAnswerEvaluation.model_validate(parse_json_object(raw))
    except (ValidationError, ValueError, TypeError) as error:
        raise InterviewEvaluationProviderError(
            "The evaluation provider returned invalid structured data."
        ) from error


def _unique_strings(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = item.strip()
        if cleaned and cleaned.casefold() not in seen:
            seen.add(cleaned.casefold())
            result.append(cleaned)
    return result


def _response(
    evaluation: InterviewAnswerEvaluation,
    *,
    answer: Any | None = None,
    question: Any | None = None,
    parent_question: Any | None = None,
    parent_answer: Any | None = None,
) -> AnswerEvaluationResponse:
    response = AnswerEvaluationResponse.model_validate(evaluation)
    if answer is None or question is None:
        return response

    question_order = getattr(question, "question_order", None)
    conversation_order = getattr(question, "conversation_order", None)
    values = response.model_dump()
    values.update(
        {
            "question": question.question,
            "answer": answer.answer,
            "question_category": question.question_category,
            "difficulty": question.difficulty,
            "question_order": question_order,
            "conversation_order": (
                float(conversation_order)
                if conversation_order is not None
                else None
            ),
            "is_follow_up": getattr(question, "is_follow_up", False),
            "parent_question_id": getattr(question, "parent_question_id", None),
            "parent_question": (
                parent_question.question if parent_question is not None else None
            ),
            "parent_answer": (
                parent_answer.answer if parent_answer is not None else None
            ),
        }
    )
    return AnswerEvaluationResponse(**values)


def _response_for_session(
    evaluation: InterviewAnswerEvaluation,
    session_record: Any,
) -> AnswerEvaluationResponse:
    answer = next(
        (item for item in session_record.answers if item.id == evaluation.answer_id),
        None,
    )
    question = next(
        (
            item
            for item in session_record.questions
            if item.id == evaluation.question_id
        ),
        None,
    )
    if answer is None or question is None:
        return _response(evaluation)

    parent_question = None
    parent_answer = None
    if question.is_follow_up and question.parent_question_id is not None:
        parent_question = next(
            (
                item
                for item in session_record.questions
                if item.id == question.parent_question_id
            ),
            None,
        )
        if parent_question is not None:
            parent_answer = next(
                (
                    item
                    for item in session_record.answers
                    if item.session_question_id == parent_question.id
                ),
                None,
            )

    return _response(
        evaluation,
        answer=answer,
        question=question,
        parent_question=parent_question,
        parent_answer=parent_answer,
    )


def _validate_provider_payload(
    payload: ProviderAnswerEvaluation,
    *,
    answer: Any,
    question: Any,
    competency: Any,
    criteria: list[Any],
) -> dict[str, Any]:
    """Validate provider identifiers, rubric coverage, and grounded evidence."""
    if payload.answer_id != answer.id or payload.question_id != question.id:
        raise InterviewEvaluationProviderError(
            "The provider response identifiers do not match the answer."
        )
    if payload.competency_reference.casefold() != competency.name.casefold():
        raise InterviewEvaluationProviderError(
            "The provider referenced an unsupported competency."
        )

    criterion_map = {criterion.criterion_id: criterion for criterion in criteria}
    returned_ids = [item.criterion_id for item in payload.criterion_evaluations]
    if len(returned_ids) != len(set(returned_ids)):
        raise InterviewEvaluationProviderError(
            "The provider returned duplicate criterion evaluations."
        )
    if set(returned_ids) != set(criterion_map):
        raise InterviewEvaluationProviderError(
            "The provider did not evaluate exactly the configured criteria."
        )

    for item in payload.criterion_evaluations:
        criterion = criterion_map[item.criterion_id]
        if item.criterion_name.casefold() != criterion.name.casefold():
            raise InterviewEvaluationProviderError(
                "The provider returned an incorrect criterion name."
            )
        for excerpt in item.evidence_excerpts:
            if excerpt not in answer.answer:
                raise InterviewEvaluationProviderError(
                    "An evidence excerpt was not found in the answer."
                )
    return criterion_map


class InterviewEvaluationScorecardService:
    """Generate persisted, rubric-grounded advisory evaluations."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.execution_repository = InterviewExecutionRepository(session)
        self.evaluation_repository = InterviewEvaluationRepository(session)

    def _get_session(self, session_id: int):
        record = self.execution_repository.get_by_id(session_id)
        if record is None:
            raise InterviewExecutionSessionNotFoundError(
                "The requested interview session was not found."
            )
        return record

    def _build_scorecard_data(
        self,
        *,
        session_record: Any,
        blueprint: Any,
        evaluations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        answer_ids = {answer.id for answer in session_record.answers}
        evaluated_ids = {item["answer_id"] for item in evaluations}
        pending_ids = sorted(answer_ids - evaluated_ids)

        competency_scores: list[dict[str, Any]] = []
        weighted_values: list[tuple[float, int]] = []
        for competency in blueprint.competencies:
            matching = [
                item["weighted_score"]
                for item in evaluations
                if item["competency_reference"].casefold()
                == competency.name.casefold()
            ]
            if not matching:
                continue
            score = round(sum(matching) / len(matching), 2)
            competency_scores.append(
                {
                    "competency_reference": competency.name,
                    "competency_weight_percent": competency.weight_percent,
                    "evaluated_answer_count": len(matching),
                    "score": score,
                }
            )
            weighted_values.append((score, competency.weight_percent))

        total_weight = sum(weight for _, weight in weighted_values)
        overall_score = (
            round(
                sum(score * weight for score, weight in weighted_values)
                / total_weight,
                2,
            )
            if total_weight
            else None
        )
        if not evaluations:
            status = ScorecardStatus.PENDING
        elif pending_ids:
            status = ScorecardStatus.PARTIAL
        else:
            status = ScorecardStatus.COMPLETE

        return {
            "status": status,
            "overall_score": overall_score,
            "evaluated_answer_count": len(evaluations),
            "pending_answer_ids": pending_ids,
            "competency_scores": competency_scores,
            "strengths": _unique_strings(
                [item for evaluation in evaluations for item in evaluation["strengths"]]
            ),
            "improvement_areas": _unique_strings(
                [
                    item
                    for evaluation in evaluations
                    for item in evaluation["improvement_areas"]
                ]
            ),
        }

    def _scorecard_response(
        self,
        *,
        session_id: int,
        session_record: Any,
        blueprint: Any,
        evaluations: list[InterviewAnswerEvaluation],
    ) -> InterviewScorecardResponse:
        data = self._build_scorecard_data(
            session_record=session_record,
            blueprint=blueprint,
            evaluations=[
                {
                    "answer_id": evaluation.answer_id,
                    "weighted_score": float(evaluation.weighted_score),
                    "competency_reference": evaluation.competency_reference,
                    "strengths": evaluation.strengths,
                    "improvement_areas": evaluation.improvement_areas,
                }
                for evaluation in evaluations
            ],
        )
        return InterviewScorecardResponse(
            session_id=session_id,
            **data,
            answer_evaluations=[
                _response_for_session(item, session_record)
                for item in evaluations
            ],
        )

    def evaluate_answer(
        self,
        *,
        session_id: int,
        answer_id: int,
        provider: LLMGenerationProvider | None = None,
    ) -> AnswerEvaluationResponse:
        session_record = self._get_session(session_id)
        answer = next(
            (item for item in session_record.answers if item.id == answer_id),
            None,
        )
        if answer is None:
            raise InterviewAnswerNotFoundForEvaluationError(
                "The requested answer was not found for this session."
            )
        existing = self.evaluation_repository.get_by_answer_id(
            session_id,
            answer_id,
        )
        if existing is not None:
            return _response(existing)

        question = next(
            (
                item
                for item in session_record.questions
                if item.id == answer.session_question_id
            ),
            None,
        )
        if question is None:
            raise InterviewEvaluationError(
                "The answer's interview question was not found."
            )

        blueprint = InterviewBlueprintRepository(self.session).get_by_id(
            session_record.blueprint_id
        )
        if blueprint is None:
            raise InterviewEvaluationError(
                "The source interview blueprint was not found."
            )
        parent_question = question
        if question.is_follow_up and question.parent_question_id is not None:
            parent_question = next(
                (
                    item
                    for item in session_record.questions
                    if item.id == question.parent_question_id
                ),
                None,
            )
            if parent_question is None:
                raise InterviewEvaluationError(
                    "The follow-up question's parent was not found."
                )

        blueprint_question_id = parent_question.blueprint_question_id
        blueprint_question = next(
            (
                item
                for item in blueprint.questions
                if item.id == blueprint_question_id
            ),
            None,
        )
        rubric_ids = list(
            getattr(blueprint_question, "rubric_criteria", []) or []
        )
        criteria = [
            criterion
            for criterion in blueprint.rubric
            if criterion.criterion_id in rubric_ids
        ]
        if not criteria:
            raise InterviewEvaluationError(
                "No usable rubric criteria are configured for this question."
            )

        competency = next(
            (
                item
                for item in blueprint.competencies
                if item.name.casefold() == parent_question.target_competency.casefold()
            ),
            None,
        )
        if competency is None:
            raise InterviewEvaluationError(
                "The question references an unsupported competency."
            )

        parent_answer = None
        if parent_question.id != question.id:
            parent_answer = next(
                (
                    item
                    for item in session_record.answers
                    if item.session_question_id == parent_question.id
                ),
                None,
            )
        analysis = ResumeAnalysisRepository(self.session).get_by_resume_id(
            blueprint.resume_id
        )
        if analysis is None:
            raise InterviewResumeAnalysisNotFoundError(
                "No persisted resume analysis was found."
            )
        job = JobRepository(self.session).get_by_id(blueprint.job_id)
        if job is None:
            raise InterviewJobNotFoundError("The source job was not found.")

        structured_resume = StructuredResume.model_validate(
            analysis.structured_resume
        )
        categorized_skills = CategorizedSkillResult.model_validate(
            analysis.categorized_skills
        )
        prompt = build_answer_evaluation_prompt(
            question=question,
            answer=answer,
            parent_question=(parent_question if question.is_follow_up else None),
            parent_answer=parent_answer,
            competency=competency,
            criteria=criteria,
            job=job,
            structured_resume=structured_resume,
            categorized_skills=categorized_skills,
        )
        rollback = getattr(self.session, "rollback", None)
        if callable(rollback):
            rollback()
        active_provider = provider or get_ollama_generation_provider()
        provider_name = type(active_provider).__name__
        payload = None
        criterion_map = None
        for attempt in range(2):
            attempt_prompt = prompt
            if attempt:
                attempt_prompt += (
                    "\n\nYour previous response was rejected. Return one corrected "
                    "JSON object only. Evaluate every configured criterion exactly "
                    "once, use scores from 0 to 5, and include evidence excerpts "
                    "that occur verbatim in the submitted answer."
                )
            raw = generate_structured_text(
                active_provider,
                system_prompt=(
                    "You are a careful CareerLens interview evaluator. "
                    "Return only the requested evidence-grounded JSON."
                ),
                prompt=attempt_prompt,
                response_schema=ProviderAnswerEvaluation.model_json_schema(),
            )
            try:
                candidate = _parse_provider_output(raw)
                candidate_criteria = _validate_provider_payload(
                    candidate,
                    answer=answer,
                    question=question,
                    competency=competency,
                    criteria=criteria,
                )
                payload = candidate
                criterion_map = candidate_criteria
                break
            except InterviewEvaluationProviderError:
                if attempt == 1:
                    raise

        if payload is None or criterion_map is None:
            raise InterviewEvaluationProviderError(
                "The evaluation provider returned invalid structured data."
            )

        weighted_score = 0.0
        criterion_rows: list[dict] = []
        for item in payload.criterion_evaluations:
            criterion = criterion_map[item.criterion_id]
            weighted_score += item.score * criterion.weight_percent / 100
            criterion_rows.append(
                {
                    "criterion_id": item.criterion_id,
                    "criterion_name": criterion.name,
                    "score": item.score,
                    "explanation": item.explanation,
                    "evidence_excerpts": item.evidence_excerpts,
                    "improvement_suggestion": item.improvement_suggestion,
                }
            )
        weighted_score = round(weighted_score, 2)

        previous = self.evaluation_repository.list_by_session_id(session_id)
        existing_data = [
            {
                "answer_id": evaluation.answer_id,
                "weighted_score": float(evaluation.weighted_score),
                "competency_reference": evaluation.competency_reference,
                "strengths": evaluation.strengths,
                "improvement_areas": evaluation.improvement_areas,
            }
            for evaluation in previous
        ]
        existing_data.append(
            {
                "answer_id": answer.id,
                "weighted_score": weighted_score,
                "competency_reference": competency.name,
                "strengths": payload.strengths,
                "improvement_areas": payload.improvement_areas,
            }
        )
        scorecard_data = self._build_scorecard_data(
            session_record=session_record,
            blueprint=blueprint,
            evaluations=existing_data,
        )
        evaluation = self.evaluation_repository.persist_evaluation(
            session_id=session_id,
            answer_id=answer.id,
            question_id=question.id,
            competency_reference=competency.name,
            weighted_score=weighted_score,
            strengths=_unique_strings(payload.strengths),
            improvement_areas=_unique_strings(payload.improvement_areas),
            actionable_feedback=_unique_strings(payload.actionable_feedback),
            provider_name=provider_name,
            criterion_rows=criterion_rows,
            scorecard=scorecard_data,
        )
        return _response(
            evaluation,
            answer=answer,
            question=question,
            parent_question=(parent_question if question.is_follow_up else None),
            parent_answer=parent_answer,
        )

    def get_answer_evaluation(
        self,
        *,
        session_id: int,
        answer_id: int,
    ) -> AnswerEvaluationResponse:
        """Return one persisted evaluation after validating session ownership."""
        session_record = self._get_session(session_id)
        if not any(answer.id == answer_id for answer in session_record.answers):
            raise InterviewAnswerNotFoundForEvaluationError(
                "The requested answer was not found for this session."
            )
        evaluation = self.evaluation_repository.get_by_answer_id(
            session_id,
            answer_id,
        )
        if evaluation is None:
            raise InterviewEvaluationError(
                "The requested answer has not been evaluated yet."
            )
        return _response_for_session(evaluation, session_record)

    def get_scorecard(self, session_id: int) -> InterviewScorecardResponse:
        session_record = self._get_session(session_id)
        blueprint = InterviewBlueprintRepository(self.session).get_by_id(
            session_record.blueprint_id
        )
        if blueprint is None:
            raise InterviewEvaluationError(
                "The source interview blueprint was not found."
            )
        evaluations = self.evaluation_repository.list_by_session_id(session_id)
        get_persisted_scorecard = getattr(
            self.evaluation_repository,
            "get_scorecard",
            None,
        )
        persisted_scorecard = (
            get_persisted_scorecard(session_id)
            if callable(get_persisted_scorecard)
            else None
        )
        if persisted_scorecard is not None:
            return InterviewScorecardResponse(
                session_id=session_id,
                status=persisted_scorecard.status,
                overall_score=(
                    float(persisted_scorecard.overall_score)
                    if persisted_scorecard.overall_score is not None
                    else None
                ),
                evaluated_answer_count=persisted_scorecard.evaluated_answer_count,
                pending_answer_ids=list(persisted_scorecard.pending_answer_ids),
                competency_scores=[
                    CompetencyScoreResponse.model_validate(item)
                    for item in persisted_scorecard.competency_scores
                ],
                answer_evaluations=[
                    _response_for_session(item, session_record)
                    for item in evaluations
                ],
                strengths=list(persisted_scorecard.strengths),
                improvement_areas=list(persisted_scorecard.improvement_areas),
            )
        return self._scorecard_response(
            session_id=session_id,
            session_record=session_record,
            blueprint=blueprint,
            evaluations=evaluations,
        )
