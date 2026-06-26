"""[여원] 플랫폼 등록 관련 스키마."""

import uuid

from pydantic import BaseModel


class PublishRequest(BaseModel):
    """상품을 등록할 대상 플랫폼 목록."""
    platforms: list[str]


class PlatformAccountOut(BaseModel):
    id: uuid.UUID
    platform: str
    is_active: bool

    model_config = {"from_attributes": True}
