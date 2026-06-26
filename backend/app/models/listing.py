import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class ListingStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    sold = "sold"
    removed = "removed"


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id"), nullable=False)
    platform_account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("platform_accounts.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    platform_product_id: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    status: Mapped[ListingStatus] = mapped_column(Enum(ListingStatus), default=ListingStatus.pending)
    listed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    product: Mapped["Product"] = relationship(back_populates="listings")
    platform_account: Mapped["PlatformAccount"] = relationship(back_populates="listings")
    sale: Mapped["Sale | None"] = relationship(back_populates="listing")
