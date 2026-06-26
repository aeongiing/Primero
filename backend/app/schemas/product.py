import uuid
from datetime import datetime
from typing import List, Optional

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
    colors: List[str] = []
    materials: List[str] = []
    size: Optional[str] = None
    chest: Optional[int] = None
    total_length: Optional[int] = None
    waist: Optional[int] = None
    hip: Optional[int] = None
    rise: Optional[int] = None
    platforms: List[str]  # 등록할 플랫폼 목록


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = Field(default=None, gt=0)
    condition: Optional[int] = Field(default=None, ge=1, le=10)


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
    colors: List[str] = []
    materials: List[str] = []
    size: Optional[str]
    chest: Optional[int]
    total_length: Optional[int]
    waist: Optional[int]
    hip: Optional[int]
    rise: Optional[int]
    created_at: datetime
    images: List[ProductImageOut] = []

    model_config = {"from_attributes": True}
