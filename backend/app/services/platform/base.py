"""[여원] 플랫폼 어댑터 추상 인터페이스.

각 중고거래 플랫폼(당근/번개/Fruits/차란/eBay)은 이 인터페이스를
구현한다. 등록/조회/삭제 3개 동작을 표준화한다.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ListingPayload:
    """플랫폼에 등록할 상품 데이터."""
    title: str
    description: str
    price: int
    category: str
    image_keys: list[str]


class PlatformAdapter(ABC):
    """플랫폼별 등록/동기화 어댑터."""

    platform: str

    @abstractmethod
    async def create_listing(self, credential_key: str, payload: ListingPayload) -> str:
        """등록 후 플랫폼 측 상품 ID 반환."""
        ...

    @abstractmethod
    async def is_sold(self, credential_key: str, platform_product_id: str) -> bool:
        """판매 완료 여부 폴링."""
        ...

    @abstractmethod
    async def delete_listing(self, credential_key: str, platform_product_id: str) -> None:
        """플랫폼에서 상품 삭제."""
        ...
