from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.job_explanation import AIJobExplanationResponse
from app.models.match_explaination import MatchExplanationResponse
from app.services.hybrid_matching_service import (
    JobNotFoundError,
    ResumeAnalysisNotFoundError,
)
from app.services.job_explanation_generator import JobExplanationGenerator
from app.services.llm.ollama_generator import OllamaGenerationProvider
from app.services.match_explaination_service import explain_match
from app.repositories.job_repository import JobRepository


router = APIRouter()


@router.get(
    "/matching/resumes/{resume_id}/jobs/{job_id}/explanation",
    response_model=MatchExplanationResponse,
)
def get_match_explanation(
    resume_id: int,
    job_id: int,
    db: Session = Depends(get_db),
) -> MatchExplanationResponse:
    """Return an explainable summary of a hybrid match."""
    try:
        return explain_match(
            resume_id=resume_id,
            job_id=job_id,
            session=db,
        )
    except ResumeAnalysisNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except JobNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="The match explanation could not be calculated.",
        ) from error


@router.get(
    "/matching/resumes/{resume_id}/jobs/{job_id}/ai-explanation",
    response_model=AIJobExplanationResponse,
)
def get_ai_job_explanation(
    resume_id: int,
    job_id: int,
    db: Session = Depends(get_db),
) -> AIJobExplanationResponse:
    """Generate a grounded natural-language explanation using Ollama."""
    try:
        explanation = explain_match(
            resume_id=resume_id,
            job_id=job_id,
            session=db,
        )

        job_repository = JobRepository(db)
        job = job_repository.get_by_id(job_id)

        if job is None:
            raise JobNotFoundError("The requested job was not found.")

        provider = OllamaGenerationProvider()

        generator = JobExplanationGenerator(
            provider=provider,
        )

        ai_explanation = generator.generate(
            explanation=explanation,
            job_title=job.title,
            company=job.company,
        )

        return AIJobExplanationResponse(
            resume_id=explanation.resume_id,
            job_id=explanation.job_id,
            hybrid_score=explanation.hybrid_score,
            explanation=ai_explanation,
        )

    except ResumeAnalysisNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except JobNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=500,
            detail="The AI job explanation could not be generated.",
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="The AI explanation service is currently unavailable.",
        ) from error