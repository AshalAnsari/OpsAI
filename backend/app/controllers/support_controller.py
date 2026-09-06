from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.rbac import require_admin, require_customer
from app.models.role import User
from app.models.support import TicketStatus
from app.schemas.support import TicketCreate, TicketMessageCreate, TicketStatusUpdate
from app.services.support_service import SupportService
from app.utils.pagination import PaginationParams

router = APIRouter(tags=["Support"])


@router.post("/support/tickets", summary="Create a support ticket")
def create_ticket(
    payload: TicketCreate,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    data = SupportService(db).create_ticket(current_user, payload)
    return {"success": True, "data": data}


@router.get("/support/tickets", summary="List my support tickets")
def list_my_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    pagination = PaginationParams(page=page, page_size=page_size)
    data = SupportService(db).list_customer_tickets(current_user, pagination)
    return {"success": True, "data": data}


@router.get("/support/tickets/{ticket_id}", summary="Get my support ticket")
def get_my_ticket(
    ticket_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    data = SupportService(db).get_customer_ticket(current_user, ticket_id)
    return {"success": True, "data": data}


@router.post("/support/tickets/{ticket_id}/messages", summary="Reply to my ticket")
def reply_my_ticket(
    ticket_id: int,
    payload: TicketMessageCreate,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    data = SupportService(db).customer_reply(current_user, ticket_id, payload)
    return {"success": True, "data": data}


@router.get("/admin/support/tickets", summary="List all support tickets", tags=["Admin"])
def admin_list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: TicketStatus | None = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    pagination = PaginationParams(page=page, page_size=page_size)
    data = SupportService(db).list_admin_tickets(pagination, status)
    return {"success": True, "data": data}


@router.get("/admin/support/tickets/{ticket_id}", summary="Get support ticket", tags=["Admin"])
def admin_get_ticket(
    ticket_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    data = SupportService(db).get_admin_ticket(ticket_id)
    return {"success": True, "data": data}


@router.post(
    "/admin/support/tickets/{ticket_id}/messages",
    summary="Admin reply (emails customer + in-app notification)",
    tags=["Admin"],
)
def admin_reply_ticket(
    ticket_id: int,
    payload: TicketMessageCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    data = SupportService(db).admin_reply(current_user, ticket_id, payload)
    return {"success": True, "data": data}


@router.patch(
    "/admin/support/tickets/{ticket_id}/status",
    summary="Update ticket status",
    tags=["Admin"],
)
def admin_update_ticket_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    data = SupportService(db).update_status(current_user, ticket_id, payload)
    return {"success": True, "data": data}
