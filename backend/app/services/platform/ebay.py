"""[여원] eBay 어댑터.

eBay는 공식 API 사용이 가능하므로 OpenClaw 대신 직접 API 연동을
고려할 수 있다(인터페이스는 동일).
"""

from app.services.platform.base import PlatformAdapter, ListingPayload


class EbayAdapter(PlatformAdapter):
    platform = "ebay"

    async def create_listing(self, credential_key: str, payload: ListingPayload) -> str:
        raise NotImplementedError

    async def is_sold(self, credential_key: str, platform_product_id: str) -> bool:
        raise NotImplementedError

    async def delete_listing(self, credential_key: str, platform_product_id: str) -> None:
        raise NotImplementedError
