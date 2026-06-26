import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.product import ProductStatus


class ProductImageOut(BaseModel):
    id: uuid.UUID
    s3_key: str
    order: int

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    title: str
    brand: str
    description: str
    category: str
    condition: int = Field(ge=1, le=10)
    price: int = Field(gt=0)
    size: str | None = None
    chest: int | None = None
    total_length: int | None = None
    waist: int | None = None
    hip: int | None = None
    rise: int | None = None
    platforms: list[str]  # 등록할 플랫폼 목록


class ProductUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    price: int | None = Field(default=None, gt=0)
    condition: int | None = Field(default=None, ge=1, le=10)


class ProductOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    brand: str
    description: str
    category: str
    condition: int
    price: int
    status: ProductStatus
    size: str | None
    chest: int | None
    total_length: int | None
    waist: int | None
    hip: int | None
    rise: int | None
    created_at: datetime
    images: list[ProductImageOut] = []

    model_config = {"from_attributes": True}
