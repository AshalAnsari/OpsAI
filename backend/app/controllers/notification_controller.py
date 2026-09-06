from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models.role import User
from app.services.notification_service import NotificationService
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", summary="List my notifications (excludes expired > 7 days)")
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    pagination = PaginationParams(page=page, page_size=page_size)
    data = NotificationService(db).list_notifications(current_user.id, pagination)
    return {"success": True, "data": data}


@router.get("/unread-count", summary="Unread notification count")
def unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = NotificationService(db).unread_count(current_user.id)
    return {"success": True, "data": data}


@router.post("/{notification_id}/read", summary="Mark notification as read")
def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = NotificationService(db).mark_read(current_user.id, notification_id)
    return {"success": True, "data": data}


@router.post("/read-all", summary="Mark all notifications as read")
def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = NotificationService(db).mark_all_read(current_user.id)
    return {"success": True, "data": data}
