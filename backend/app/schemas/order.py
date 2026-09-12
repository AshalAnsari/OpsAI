from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.models.order import OrderStatus, PaymentStatus


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreateRequest(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)
    shipping_address_line1: str = Field(min_length=3, max_length=200)
    shipping_address_line2: str | None = Field(default=None, max_length=200)
    shipping_city: str = Field(min_length=2, max_length=100)
    shipping_state: str | None = Field(default=None, max_length=100)
    shipping_postal_code: str = Field(min_length=2, max_length=20)
    shipping_country: str = Field(min_length=2, max_length=2)
    shipping_country_name: str | None = Field(default=None, max_length=100)

    @field_validator("shipping_country")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if len(cleaned) != 2 or not cleaned.isalpha():
            raise ValueError("shipping_country must be a 2-letter country code")
        return cleaned

    @field_validator("shipping_address_line1", "shipping_city", "shipping_postal_code")
    @classmethod
    def strip_required(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field is required")
        return cleaned

    @field_validator(
        "shipping_address_line2",
        "shipping_state",
        "shipping_country_name",
        mode="before",
    )
    @classmethod
    def strip_optional_text(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str | None = None
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    display_id: str
    customer_id: int
    status: OrderStatus
    payment_status: PaymentStatus
    total_amount: Decimal
    shipping_address_line1: str | None = None
    shipping_address_line2: str | None = None
    shipping_city: str | None = None
    shipping_state: str | None = None
    shipping_postal_code: str | None = None
    shipping_country: str
    shipping_country_name: str | None = None
    current_location: str | None = None
    status_changed_at: datetime | None = None
    stripe_checkout_session_id: str | None = None
    checkout_url: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []

    model_config = {"from_attributes": True}


class OrderCreateResponse(BaseModel):
    order: OrderResponse
    checkout_url: str
    message: str = "Demo checkout created. Complete payment in Stripe sandbox to confirm the order."


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class FulfillmentAdvanceResponse(BaseModel):
    advanced_count: int
    run_date: str
    triggered_by: str
    skipped: bool = False
    message: str
