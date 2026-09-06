from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, EmailStr

from app.schemas.order import OrderResponse
from app.schemas.user import AdminCustomerResponse


class DashboardMetrics(BaseModel):
    total_customers: int
    total_orders: int
    pending_orders: int
    processing_orders: int
    delivered_orders: int
    cancelled_orders: int
    total_revenue: Decimal
    recent_orders: list[OrderResponse]
    recent_customers: list[AdminCustomerResponse]
    recent_audit_logs: list["AuditLogResponse"]


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    user_email: EmailStr | None = None
    action: str
    entity_type: str
    entity_id: str | None
    metadata: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminOrderDetailResponse(OrderResponse):
    customer_email: EmailStr | None = None
    customer_name: str | None = None
