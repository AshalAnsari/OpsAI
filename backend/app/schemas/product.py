from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=220)
    description: str = ""
    price: Decimal = Field(gt=0)
    stock_quantity: int = Field(ge=0)
    is_active: bool = True
    image_urls: list[str] = Field(default_factory=list)
    specs: dict[str, str] = Field(default_factory=dict)

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for url in value:
            url = url.strip()
            if not url:
                continue
            if not (url.startswith("http://") or url.startswith("https://")):
                raise ValueError("Image URLs must start with http:// or https://")
            cleaned.append(url)
        return cleaned


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=220)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None
    image_urls: list[str] | None = None
    specs: dict[str, str] | None = None

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return ProductCreate.validate_image_urls(value)


class ProductResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    price: Decimal
    stock_quantity: int
    is_active: bool
    image_urls: list[str] = []
    specs: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
