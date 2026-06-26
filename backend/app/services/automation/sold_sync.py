"""[여원] 판매 완료 동기화.

한 플랫폼에서 판매 완료가 감지되면 나머지 플랫폼의 리스팅을 자동
삭제하고 상품 상태를 sold 로 전환한다.
"""

import uuid


async def sync_sold(product_id: uuid.UUID, sold_listing_id: uuid.UUID) -> None:
    """판매된 리스팅을 제외한 나머지 플랫폼에서 상품을 삭제한다.

    TODO:
      - product 의 active 리스팅 조회
      - sold_listing 제외 전부 adapter.delete_listing 호출
      - Product.status = sold, 나머지 Listing.status = removed
    """
    raise NotImplementedError
