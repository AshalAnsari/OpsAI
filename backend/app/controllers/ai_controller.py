from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.service import run_support_turn
from app.core.database import get_db
from app.dependencies.rbac import require_customer
from app.models.role import User
from app.schemas.ai import AISupportChatRequest, AISupportChatResponse

router = APIRouter(prefix="/ai", tags=["AI Support"])


@router.post(
    "/support/chat",
    summary="Harbor Dock Station AI Support (LangGraph + tools)",
    response_model=None,
)
def ai_support_chat(
    payload: AISupportChatRequest,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
) -> dict:
    """
    Day 2+ AI OS Mini entrypoint.

    Flow: classify -> tools/RAG via FastAPI services -> answer -> optional ticket escalation.
    Never auto-refunds. Customer JWT enforces order ownership.
    """
    data = run_support_turn(
        db,
        current_user,
        payload.message,
        confirm_cancel=payload.confirm_cancel,
        order_id_hint=payload.order_id_hint,
    )
    # Validate shape for docs / clients
    AISupportChatResponse.model_validate(data)
    return {"success": True, "data": data}
