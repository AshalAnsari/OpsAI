from datetime import datetime

from pydantic import BaseModel, Field

from app.models.support import TicketStatus


class TicketCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=5, max_length=5000)


class TicketMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class SupportMessageResponse(BaseModel):
    id: int
    ticket_id: int
    sender_id: int
    sender_name: str | None = None
    body: str
    is_staff: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SupportTicketResponse(BaseModel):
    id: int
    display_id: str
    customer_id: int
    customer_email: str | None = None
    customer_name: str | None = None
    subject: str
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    messages: list[SupportMessageResponse] = []

    model_config = {"from_attributes": True}
