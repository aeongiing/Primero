import uuid

from pydantic import BaseModel


class ImageUploadOut(BaseModel):
    id: uuid.UUID
    s3_key: str
    order: int

    model_config = {"from_attributes": True}
