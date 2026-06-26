"""[여원] eBay 어댑터.

eBay 는 공식 API 사용이 가능하므로 브라우저 자동화 대신 직접 API 연동을
고려한다(인터페이스는 동일). MVP 우선순위상 추후 구현 대상이다.
"""

from app.services.platform.base import ListingPayload, PlatformAdapter
from app.services.platform.browser import Credentials


class EbayAdapter(PlatformAdapter):
    platform = "ebay"

    async def create_listing(self, credentials: Credentials, payload: ListingPayload) -> str:
        raise NotImplementedError

    async def is_sold(self, credentials: Credentials, platform_product_id: str) -> bool:
        raise NotImplementedError

    async def delete_listing(self, credentials: Credentials, platform_product_id: str) -> None:
        raise NotImplementedError

    async def update_price(self, credentials: Credentials, platform_product_id: str, new_price: int) -> None:
        raise NotImplementedError
