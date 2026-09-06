from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import TokenDecodeError, get_subject_from_token
from app.models.role import User
from app.repositories.user_repository import UserRepository
from app.utils.exceptions import AppError

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("UNAUTHENTICATED", "Authentication required.", 401)

    try:
        subject = get_subject_from_token(credentials.credentials)
        user_id = int(subject)
    except (TokenDecodeError, ValueError) as exc:
        raise AppError("INVALID_TOKEN", "Invalid or expired access token.", 401) from exc

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise AppError("UNAUTHENTICATED", "User not found or inactive.", 401)
    return user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        return get_current_user(credentials, db)
    except AppError:
        return None
