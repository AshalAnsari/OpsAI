from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    roles: list[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerProfileResponse(UserResponse):
    order_count: int = 0
    paid_order_count: int = 0
    pending_orders: int = 0
    delivered_orders: int = 0
    cancelled_orders: int = 0
    total_spent: float = 0.0
    average_order_value: float = 0.0
    initials: str = ""


class AdminCustomerResponse(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime
    order_count: int = 0
    total_spent: float = 0.0

    model_config = {"from_attributes": True}
