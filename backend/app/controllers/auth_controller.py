from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.role import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=dict,
    summary="Register a new customer account",
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    token, user = AuthService(db).register(payload)
    return {"success": True, "data": {"token": token, "user": user}}


@router.post(
    "/login",
    response_model=dict,
    summary="Login and receive a JWT access token",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> dict:
    token, user = AuthService(db).login(payload)
    return {"success": True, "data": {"token": token, "user": user}}


@router.get(
    "/me",
    response_model=dict,
    summary="Get the authenticated user and roles",
)
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    user = AuthService(db).get_me(current_user)
    return {"success": True, "data": user}
