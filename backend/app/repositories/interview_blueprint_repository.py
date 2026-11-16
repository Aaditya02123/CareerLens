from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.models.interview_blueprint import (
    BlueprintCompetency,
    BlueprintCompetencyDraft,
    BlueprintQuestion,
    BlueprintQuestionDraft,
    BlueprintRubricCriterion,
    BlueprintRubricCriterionDraft,
    InterviewBlueprint,
)


class InterviewBlueprintRepository:
    """Persistence operations for interview blueprints and children."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        resume_id: int,
        job_id: int,
        target_role: str,
        interview_type: str,
        difficulty: str,
        duration_minutes: int,
        question_count: int,
        competencies: list[BlueprintCompetencyDraft],
        questions: list[BlueprintQuestionDraft],
        rubric: list[BlueprintRubricCriterionDraft],
    ) -> InterviewBlueprint:
        """Persist a complete blueprint atomically."""
        blueprint = InterviewBlueprint(
            resume_id=resume_id,
            job_id=job_id,
            target_role=target_role,
            interview_type=interview_type,
            difficulty=difficulty,
            duration_minutes=duration_minutes,
            question_count=question_count,
        )
        self.session.add(blueprint)

        try:
            self.session.flush()

            for competency in competencies:
                self.session.add(
                    BlueprintCompetency(
                        blueprint_id=blueprint.id,
                        **competency.model_dump(),
                    )
                )

            for question_order, question in enumerate(questions, start=1):
                self.session.add(
                    BlueprintQuestion(
                        blueprint_id=blueprint.id,
                        question_order=question_order,
                        **question.model_dump(),
                    )
                )

            for criterion in rubric:
                self.session.add(
                    BlueprintRubricCriterion(
                        blueprint_id=blueprint.id,
                        **criterion.model_dump(),
                    )
                )

            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise

        return self.get_by_id(blueprint.id) or blueprint

    def get_by_id(self, blueprint_id: int) -> InterviewBlueprint | None:
        statement = (
            select(InterviewBlueprint)
            .options(
                selectinload(InterviewBlueprint.competencies),
                selectinload(InterviewBlueprint.questions),
                selectinload(InterviewBlueprint.rubric),
            )
            .where(InterviewBlueprint.id == blueprint_id)
        )
        return self.session.scalar(statement)

    def list_by_resume_id(
        self,
        resume_id: int,
        *,
        offset: int = 0,
        limit: int = 50,
        job_id: int | None = None,
    ) -> list[InterviewBlueprint]:
        statement = (
            select(InterviewBlueprint)
            .options(
                selectinload(InterviewBlueprint.competencies),
                selectinload(InterviewBlueprint.questions),
                selectinload(InterviewBlueprint.rubric),
            )
            .where(InterviewBlueprint.resume_id == resume_id)
        )
        if job_id is not None:
            statement = statement.where(InterviewBlueprint.job_id == job_id)

        statement = (
            statement
            .order_by(
                InterviewBlueprint.created_at.desc(),
                InterviewBlueprint.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def delete_by_id(self, blueprint_id: int) -> bool:
        blueprint = self.get_by_id(blueprint_id)
        if blueprint is None:
            return False

        try:
            self.session.delete(blueprint)
            self.session.commit()
        except SQLAlchemyError:
            self.session.rollback()
            raise
        return True
