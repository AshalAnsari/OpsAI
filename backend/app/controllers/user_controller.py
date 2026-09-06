from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.rbac import require_customer_or_admin
from app.models.role import User
from app.schemas.user import UserProfileUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/customer", tags=["Customer"])


@router.get("/profile", summary="Get profile with account stats")
def get_profile(
    current_user: User = Depends(require_customer_or_admin),
    db: Session = Depends(get_db),
) -> dict:
    profile = UserService(db).get_profile(current_user)
    return {"success": True, "data": profile}


@router.put("/profile", summary="Update profile name details")
def update_profile(
    payload: UserProfileUpdate,
    current_user: User = Depends(require_customer_or_admin),
    db: Session = Depends(get_db),
) -> dict:
    profile = UserService(db).update_profile(current_user, payload)
    return {"success": True, "data": profile}
