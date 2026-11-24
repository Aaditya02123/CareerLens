from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.interview_blueprint import InterviewBlueprint
from app.models.interview_execution import InterviewExecutionSession
from app.models.interview_session import InterviewSession
from app.models.learning_roadmap_db import LearningRoadmap, LearningRoadmapItem
from app.models.resume import Resume
from app.models.user import User

_bearer_scheme = HTTPBearer(auto_error=False)
_password_hash = PasswordHash.recommended()
_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
_token_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    environment = os.getenv("CAREERLENS_ENV", "development")
    if secret:
        return secret
    if environment == "development":
        return "development-only-secret-change-before-deployment"
    raise RuntimeError("JWT_SECRET must be configured outside development.")


def hash_password(password: str) -> str:
    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    return bool(password_hash) and _password_hash.verify(password, password_hash)


def create_access_token(user: User) -> str:
    expires_at = datetime.now(UTC) + timedelta(minutes=_token_minutes)
    return jwt.encode(
        {"sub": str(user.id), "exp": expires_at},
        _jwt_secret(),
        algorithm=_algorithm,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication is required.")
    try:
        payload = jwt.decode(
            credentials.credentials,
            _jwt_secret(),
            algorithms=[_algorithm],
        )
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=401, detail="Invalid authentication token.") from error

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication user no longer exists.")
    return user


def require_current_user_id(user_id: int, current_user: User) -> None:
    if user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")


def require_owned_resume(resume_id: int, current_user: User, db: Session) -> Resume:
    resume = db.get(Resume, resume_id)
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    return resume


def require_owned_resume_filename(
    stored_filename: str, current_user: User, db: Session
) -> Resume:
    resume = db.scalar(
        select(Resume).where(Resume.stored_filename == stored_filename)
    )
    if resume is None:
        raise HTTPException(status_code=404, detail="Resume not found.")
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    return resume


def require_owned_legacy_session(
    session_id: int, current_user: User, db: Session
) -> InterviewSession:
    interview_session = db.get(InterviewSession, session_id)
    if interview_session is None:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    if interview_session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    return interview_session


def require_owned_blueprint(
    blueprint_id: int, current_user: User, db: Session
) -> InterviewBlueprint:
    blueprint = db.get(InterviewBlueprint, blueprint_id)
    if blueprint is None:
        raise HTTPException(status_code=404, detail="Interview blueprint not found.")
    require_owned_resume(blueprint.resume_id, current_user, db)
    return blueprint


def require_owned_execution_session(
    session_id: int, current_user: User, db: Session
) -> InterviewExecutionSession:
    execution_session = db.get(InterviewExecutionSession, session_id)
    if execution_session is None:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    require_owned_blueprint(execution_session.blueprint_id, current_user, db)
    return execution_session


def require_owned_roadmap_item(
    item_id: int, current_user: User, db: Session
) -> LearningRoadmapItem:
    item = db.get(LearningRoadmapItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Learning roadmap item not found.")
    roadmap = db.get(LearningRoadmap, item.roadmap_id)
    if roadmap is None:
        raise HTTPException(status_code=404, detail="Learning roadmap not found.")
    require_owned_resume(roadmap.resume_id, current_user, db)
    return item
