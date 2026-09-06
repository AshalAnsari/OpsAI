"""
Demo helper to simulate Stripe webhook payment confirmation without Stripe CLI.

POST /api/v1/webhooks/stripe/demo-complete
Body: { "order_id": 1 }

Only available when STRIPE_SECRET_KEY is a placeholder (local demo mode).
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.dependencies.rbac import require_customer_or_admin
from app.models.order import OrderStatus, PaymentStatus
from app.models.role import User
from app.repositories.audit_repository import AuditRepository
from app.repositories.order_repository import OrderRepository
from app.services.fulfillment_service import apply_status_side_effects
from app.utils.exceptions import AppError

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
settings = get_settings()


class DemoCompletePaymentRequest(BaseModel):
    order_id: int = Field(gt=0)


@router.post(
    "/stripe/demo-complete",
    summary="Simulate Stripe payment success (local demo only)",
)
def demo_complete_payment(
    payload: DemoCompletePaymentRequest,
    current_user: User = Depends(require_customer_or_admin),
    db: Session = Depends(get_db),
) -> dict:
    if not settings.stripe_secret_key.startswith("sk_test_placeholder"):
        raise AppError(
            "DEMO_MODE_DISABLED",
            "Demo payment completion is only available with placeholder Stripe keys.",
            403,
        )

    orders = OrderRepository(db)
    order = orders.get_by_id(payload.order_id)
    if not order:
        raise AppError("ORDER_NOT_FOUND", "Order not found.", 404)

    if current_user.has_role("customer") and order.customer_id != current_user.id:
        raise AppError("ORDER_NOT_FOUND", "Order not found.", 404)

    if order.payment_status == PaymentStatus.PAID:
        return {"success": True, "data": {"order_id": order.id, "duplicate": True}}

    order.payment_status = PaymentStatus.PAID
    if order.status == OrderStatus.PENDING:
        apply_status_side_effects(order, OrderStatus.CONFIRMED)
    orders.update(order)
    AuditRepository(db).create(
        user_id=current_user.id,
        action="order.payment_completed",
        entity_type="order",
        entity_id=str(order.id),
        metadata={"source": "demo_complete", "simulated": True},
    )
    db.commit()
    return {
        "success": True,
        "data": {
            "order_id": order.id,
            "status": order.status.value,
            "payment_status": order.payment_status.value,
        },
    }
