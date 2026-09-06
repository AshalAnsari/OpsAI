from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: int
    title: str
    body: str
    link: str | None = None
    is_read: bool
    created_at: datetime
    expires_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    unread_count: int
