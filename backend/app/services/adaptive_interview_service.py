from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.interview_execution import (
    AdaptiveDecisionPayload,
    AdaptiveDecisionResponse,
    InterviewExecutionStatus,
    InterviewSessionQuestionResponse,
)
from app.models.resume import StructuredResume
from app.models.skills import CategorizedSkillResult
from app.repositories.interview_blueprint_repository import (
    InterviewBlueprintRepository,
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


MAX_FOLLOW_UPS_PER_QUESTION = 1
MAX_FOLLOW_UPS_PER_SESSION = 3


class AdaptiveQuestionError(ValueError):
    """Raised when an adaptive decision cannot be requested."""


class AdaptiveProviderError(RuntimeError):
    """Raised when structured adaptive output is unusable."""


def build_adaptive_decision_prompt(
    *,
    parent_question: Any,
    answer: Any,
    job: Any,
    structured_resume: StructuredResume,
    categorized_skills: CategorizedSkillResult,
    competency_names: list[str],
) -> str:
    context = {
        "original_question": {
            "text": parent_question.question,
            "category": parent_question.question_category,
            "difficulty": parent_question.difficulty,
            "competency": parent_question.target_competency,
        },
        "submitted_answer": answer.answer,
        "job": {
            "title": job.title,
            "description": job.description,
            "required_skills": job.required_skills,
            "preferred_skills": job.preferred_skills,
        },
        "structured_resume": structured_resume.model_dump(mode="json"),
        "categorized_skills": categorized_skills.model_dump(mode="json"),
        "declared_competencies": competency_names,
    }
    return (
        "Decide whether one concise follow-up question would add meaningful "
        "clarity or technical depth after the submitted answer. Return JSON "
        "only with outcome ask_follow_up or continue, a short rationale, and "
        "when needed follow_up_question, follow_up_type, and "
        "competency_reference. Do not score the answer. Do not infer "
        "personality, honesty, emotion, intelligence, employability, or hiring "
        "outcomes. Ground questions in the original question, submitted answer, "
        "job, blueprint competency, and supplied resume. Never invent candidate "
        "experience, projects, technologies, qualifications, or achievements. "
        "A follow-up must ask one related question, must not repeat the original, "
        "and must not claim unsupported candidate experience.\n\nContext:\n"
        + json.dumps(context, ensure_ascii=False, indent=2)
    )


def _parse_payload(raw: str) -> AdaptiveDecisionPayload:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = (
            cleaned.removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
    try:
        return AdaptiveDecisionPayload.model_validate_json(cleaned)
    except (ValidationError, ValueError, TypeError) as error:
        raise AdaptiveProviderError(
            "The adaptive interviewer returned invalid structured data."
        ) from error


def _question_response(question: Any) -> InterviewSessionQuestionResponse:
    return InterviewSessionQuestionResponse.model_validate(question)


class AdaptiveInterviewService:
    """Coordinate bounded, persisted adaptive interview decisions."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repository = InterviewExecutionRepository(session)

    def _get_session(self, session_id: int):
        record = self.repository.get_by_id(session_id)
        if record is None:
            raise InterviewExecutionSessionNotFoundError(
                "The requested interview session was not found."
            )
        return record

    @staticmethod
    def _decision_response(
        *,
        session_id: int,
        parent_question_id: int,
        decision: Any,
        session_record: Any,
    ) -> AdaptiveDecisionResponse:
        follow_up = None
        if decision.follow_up_question_id is not None:
            follow_up = next(
                (
                    item
                    for item in session_record.questions
                    if item.id == decision.follow_up_question_id
                ),
                None,
            )
        return AdaptiveDecisionResponse(
            session_id=session_id,
            parent_question_id=parent_question_id,
            outcome=decision.outcome,
            follow_up_question=(
                _question_response(follow_up)
                if follow_up is not None
                else None
            ),
        )

    def decide_after_answer(
        self,
        *,
        session_id: int,
        parent_question_id: int,
        provider: LLMGenerationProvider | None = None,
    ) -> AdaptiveDecisionResponse:
        record = self._get_session(session_id)
        if record.status != InterviewExecutionStatus.IN_PROGRESS:
            raise AdaptiveQuestionError(
                "Adaptive decisions are available only for in-progress sessions."
            )

        parent_question = self.repository.get_question_by_id(
            record,
            parent_question_id,
        )
        if parent_question is None or parent_question.is_follow_up:
            raise AdaptiveQuestionError(
                "The selected question is not an eligible planned question."
            )
        if self.repository.get_answer_by_question(
            session_id,
            parent_question.id,
        ) is None:
            raise AdaptiveQuestionError(
                "The planned question must be answered first."
            )

        existing = self.repository.get_adaptive_decision(
            session_id,
            parent_question.id,
        )
        if existing is not None:
            return self._decision_response(
                session_id=session_id,
                parent_question_id=parent_question.id,
                decision=existing,
                session_record=record,
            )

        follow_up_count = sum(
            1 for question in record.questions if question.is_follow_up
        )
        if follow_up_count >= MAX_FOLLOW_UPS_PER_SESSION:
            payload = AdaptiveDecisionPayload(
                outcome="continue",
                rationale="The session follow-up limit has been reached.",
            )
        else:
            blueprint = InterviewBlueprintRepository(self.session).get_by_id(
                record.blueprint_id
            )
            if blueprint is None:
                raise AdaptiveQuestionError(
                    "The source interview blueprint was not found."
                )
            answer = self.repository.get_answer_by_question(
                session_id,
                parent_question.id,
            )
            assert answer is not None
            resume_analysis = ResumeAnalysisRepository(
                self.session
            ).get_by_resume_id(
                blueprint.resume_id
            )
            if resume_analysis is None:
                raise AdaptiveQuestionError(
                    "No persisted resume analysis was found."
                )
            job = JobRepository(self.session).get_by_id(blueprint.job_id)
            if job is None:
                raise AdaptiveQuestionError("The source job was not found.")

            structured_resume = StructuredResume.model_validate(
                resume_analysis.structured_resume
            )
            categorized_skills = CategorizedSkillResult.model_validate(
                resume_analysis.categorized_skills
            )
            competency_names = [item.name for item in blueprint.competencies]
            prompt = build_adaptive_decision_prompt(
                parent_question=parent_question,
                answer=answer,
                job=job,
                structured_resume=structured_resume,
                categorized_skills=categorized_skills,
                competency_names=competency_names,
            )
            # End the read-only transaction before any potentially slow
            # provider call. The persistence transaction starts only after
            # structured output has been validated.
            rollback = getattr(self.session, "rollback", None)
            if callable(rollback):
                rollback()

            raw = (provider or get_ollama_generation_provider()).generate(
                system_prompt=(
                    "You are a careful CareerLens technical interviewer. "
                    "Return only the requested JSON decision."
                ),
                prompt=prompt,
            )
            payload = _parse_payload(raw)
            if (
                payload.competency_reference is not None
                and payload.competency_reference.casefold()
                not in {name.casefold() for name in competency_names}
            ):
                raise AdaptiveProviderError(
                    "The adaptive response referenced an unsupported competency."
                )

        locked_record = self.repository.get_by_id_for_update(session_id)
        if locked_record is None:
            raise InterviewExecutionSessionNotFoundError(
                "The requested interview session was not found."
            )
        existing = self.repository.get_adaptive_decision(
            session_id,
            parent_question.id,
        )
        if existing is not None:
            return self._decision_response(
                session_id=session_id,
                parent_question_id=parent_question.id,
                decision=existing,
                session_record=locked_record,
            )

        follow_up_data = None
        if payload.outcome == "ask_follow_up":
            follow_up_data = {
                "question": payload.follow_up_question,
                "question_category": parent_question.question_category,
                "difficulty": parent_question.difficulty,
                "target_competency": (
                    payload.competency_reference
                    or parent_question.target_competency
                ),
                "assessment_objective": (
                    "Clarify or deepen the preceding answer."
                ),
                "relevance_reason": "This follow-up is grounded in the preceding answer.",
            }

        decision = self.repository.create_adaptive_decision(
            session_record=locked_record,
            parent_question=next(
                question
                for question in locked_record.questions
                if question.id == parent_question.id
            ),
            outcome=payload.outcome,
            rationale=payload.rationale,
            follow_up_type=payload.follow_up_type,
            competency_reference=payload.competency_reference,
            follow_up_question=follow_up_data,
        )
        final_record = self.repository.get_by_id(session_id)
        assert final_record is not None
        return self._decision_response(
            session_id=session_id,
            parent_question_id=parent_question.id,
            decision=decision,
            session_record=final_record,
        )
