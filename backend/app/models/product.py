import uuid
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class ProductStatus(str, enum.Enum):
    draft = "draft"
    listing = "listing"
    listed = "listed"
    sold = "sold"
    unlisted = "unlisted"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    brand: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    condition: Mapped[int] = mapped_column(Integer, nullable=False)  # 1~10
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[ProductStatus] = mapped_column(Enum(ProductStatus), default=ProductStatus.draft)
    size: Mapped[str | None] = mapped_column(String(20))
    chest: Mapped[int | None] = mapped_column(Integer)
    total_length: Mapped[int | None] = mapped_column(Integer)
    waist: Mapped[int | None] = mapped_column(Integer)
    hip: Mapped[int | None] = mapped_column(Integer)
    rise: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="products")
    images: Mapped[list["ProductImage"]] = relationship(back_populates="product", order_by="ProductImage.order")
    listings: Mapped[list["Listing"]] = relationship(back_populates="product")
