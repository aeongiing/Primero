"""[여원] 차란 어댑터 (OpenClaw 기반)."""

from app.services.platform.base import PlatformAdapter, ListingPayload
from app.services.platform.openclaw import OpenClawClient


class CharanAdapter(PlatformAdapter):
    platform = "charan"

    def __init__(self, client: OpenClawClient | None = None):
        self.client = client or OpenClawClient()

    async def create_listing(self, credential_key: str, payload: ListingPayload) -> str:
        raise NotImplementedError

    async def is_sold(self, credential_key: str, platform_product_id: str) -> bool:
        raise NotImplementedError

    async def delete_listing(self, credential_key: str, platform_product_id: str) -> None:
        raise NotImplementedError
