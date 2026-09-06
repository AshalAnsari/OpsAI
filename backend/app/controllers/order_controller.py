from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.rbac import require_customer
from app.models.order import OrderStatus
from app.models.role import User
from app.schemas.order import OrderCreateRequest
from app.services.order_service import OrderService
from app.utils.pagination import PaginationParams

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", summary="Create order and Stripe Checkout session")
def create_order(
    payload: OrderCreateRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    """
    Creates a demo order, reserves stock, and returns a Stripe sandbox Checkout URL.
    Payment confirmation is handled asynchronously by the Stripe webhook service.
    """
    result = OrderService(db).create_order(current_user, payload)
    return {"success": True, "data": result}


@router.get("", summary="List current customer's orders")
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: OrderStatus | None = Query(None),
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    pagination = PaginationParams(page=page, page_size=page_size)
    result = OrderService(db).list_customer_orders(current_user, pagination, status)
    return {"success": True, "data": result}


@router.get("/{order_id}", summary="Get a customer order (own orders only)")
def get_order(
    order_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    order = OrderService(db).get_customer_order(current_user, order_id)
    return {"success": True, "data": order}


@router.post("/{order_id}/cancel", summary="Cancel an eligible order")
def cancel_order(
    order_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    """
    Customers may cancel orders only in `pending` or `confirmed` status.
    Stock is restored and an audit log is written.
    """
    order = OrderService(db).cancel_customer_order(current_user, order_id)
    return {"success": True, "data": order}


@router.post(
    "/{order_id}/abandon-checkout",
    summary="Abandon unpaid Stripe checkout (cancel/decline redirect)",
)
def abandon_checkout(
    order_id: int,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    """
    Called when the customer returns from Stripe with a cancelled checkout
    or after a declined card flow. Cancels the unpaid reservation and restores stock.
    """
    order = OrderService(db).abandon_unpaid_checkout(current_user, order_id)
    return {"success": True, "data": order}
