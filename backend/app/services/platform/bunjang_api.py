"""[여원] 번개장터 HTTP API 어댑터.

브라우저 없이 번개 내부 API(api.bunjang.co.kr)를 직접 호출해 등록/조회/삭제.
인증: x-bun-auth-token (사용자가 연동 시 입력한 토큰). Credentials.username 에 담아 전달.

MVP: 사진(imageId)은 비워둠(텍스트 등록부터). 사진 업로드는 추후 연결.
⚠️ 비공식 내부 API라 변경될 수 있음.
"""

import httpx

from app.services.platform.base import PlatformAdapter, ListingPayload, PlatformError
from app.services.platform.browser import Credentials
from app.services.platform.bunjang_categories import get_bunjang_category_id

_BASE_URL = "https://api.bunjang.co.kr"
_PRODUCT_URL = f"{_BASE_URL}/api/pms/v2/products"

_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://m.bunjang.co.kr",
    "referer": "https://m.bunjang.co.kr/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
    ),
}

# 컨디션 점수 라벨 → 번개 API condition 값
_CONDITION_MAP = {
    "새 상품 (미사용)": "NEW",
    "사용감 없음": "ALMOST_NEW",
    "사용감 적음": "SLIGHTLY_USED",
    "사용감 많음": "USED",
    "고장/파손 상품": "BROKEN",
}


class BunjangApiAdapter(PlatformAdapter):
    """번개장터 HTTP API 어댑터. Credentials.username = x-bun-auth-token."""

    platform = "bunjang"

    async def create_listing(self, credentials: Credentials, payload: ListingPayload) -> str:
        token = credentials.username
        if not token:
            raise PlatformError("bunjang: 인증 토큰이 없습니다(플랫폼 계정 연동 필요)")

        f = payload.fields
        category_id = f.get("category_id") or get_bunjang_category_id(f.get("category", ""))
        condition = _CONDITION_MAP.get(f.get("condition", ""), "ALMOST_NEW")

        body = {
            "categoryId": category_id,
            "common": {
                "name": f.get("title", ""),
                "description": f.get("description", ""),
                "priceOfferEnabled": True,
                "condition": condition,
                "keywords": [],
            },
            "transaction": {
                "price": int(f.get("price", 0)),
                "quantity": 1,
                "shippingFee": 0,
                "trade": {
                    "inPerson": False,
                    "freeShipping": True,
                    "isDefaultShippingFee": False,
                    "shippingSpecs": {},
                },
            },
            "location": {},
            "media": [{"imageId": i} for i in f.get("image_ids", [])],
            "option": [],
        }

        headers = {**_HEADERS, "x-bun-auth-token": token}
        async with httpx.AsyncClient() as client:
            resp = await client.post(_PRODUCT_URL, json=body, headers=headers, timeout=30)

        if resp.status_code != 200:
            raise PlatformError(f"bunjang: 등록 실패 (HTTP {resp.status_code}): {resp.text[:200]}")

        data = resp.json()
        return str(data.get("id") or data.get("pid") or data)

    async def is_sold(self, credentials: Credentials, platform_product_id: str) -> bool:
        return False

    async def delete_listing(self, credentials: Credentials, platform_product_id: str) -> None:
        token = credentials.username
        url = f"{_BASE_URL}/api/pms/v2/products/{platform_product_id}"
        headers = {**_HEADERS, "x-bun-auth-token": token}
        async with httpx.AsyncClient() as client:
            resp = await client.delete(url, headers=headers, timeout=15)
        if resp.status_code not in (200, 204):
            raise PlatformError(f"bunjang: 삭제 실패 (HTTP {resp.status_code})")

    async def update_price(self, credentials: Credentials, platform_product_id: str, new_price: int) -> None:
        token = credentials.username
        url = f"{_BASE_URL}/api/pms/v2/products/{platform_product_id}"
        headers = {**_HEADERS, "x-bun-auth-token": token}
        async with httpx.AsyncClient() as client:
            resp = await client.patch(url, json={"transaction": {"price": new_price}}, headers=headers, timeout=15)
        if resp.status_code not in (200, 204):
            raise PlatformError(f"bunjang: 가격 변경 실패 (HTTP {resp.status_code})")
