from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.stripe_webhook_service import StripeWebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post(
    "/stripe",
    summary="Stripe webhook receiver (sandbox)",
    description=(
        "Separate webhook service for payment lifecycle events. "
        "Order placement creates a Checkout Session; this endpoint confirms payment, "
        "expires unpaid checkouts, and writes audit logs."
    ),
)
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str = Header(..., alias="Stripe-Signature"),
) -> dict:
    payload = await request.body()
    service = StripeWebhookService(db)
    event = service.construct_event(payload, stripe_signature)
    result = service.handle_event(event)
    return {"success": True, "data": result}
