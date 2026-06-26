import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.listing import ListingStatus


class ListingOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    platform: str
    platform_product_id: str
    status: ListingStatus
    listed_at: datetime

    model_config = {"from_attributes": True}
