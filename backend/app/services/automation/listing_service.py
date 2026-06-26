"""[여원] 상품 발행 서비스 — API 라우트에서 호출하는 진입점.

상품 등록 후 선택된 플랫폼에 발행을 시도하고, 결과를 Listing 테이블에 기록한다.
실제 브라우저 등록이 아직 빈 셀렉터라 실패할 수 있지만, "시도 → 기록" 흐름은
동작한다. 실제 등록이 되면 상품 상태를 listed 로 전환한다.

동기 방식(API 안에서 바로 처리). 나중에 SQS 비동기로 전환 시
이 함수의 호출자만 워커로 옮기면 된다.
"""

import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.mapping import CanonicalProduct
from app.models.listing import Listing, ListingStatus
from app.models.platform_account import PlatformAccount
from app.models.product import Product, ProductStatus
from app.services.automation.publisher import publish_product, PublishStatus, PublishOutcome
from app.services.platform.base import PlatformAdapter, ListingPayload
from app.services.platform.browser import Credentials, PlaywrightBrowser
from app.services.platform.registry import get_adapter, _API_ADAPTERS
from app.core.config import settings

# 세션 파일 디렉터리 (backend/auth/)
_AUTH_DIR = Path(__file__).resolve().parent.parent.parent / "auth"


def _to_canonical(product: Product) -> CanonicalProduct:
    """ORM Product → 매핑 엔진 입력 객체로 변환."""
    return CanonicalProduct(
        title=product.title,
        brand=product.brand,
        description=product.description,
        category=product.category,
        condition=float(product.condition),
        price=product.price,
        size=product.size,
        colors=tuple(product.colors or []),
        materials=tuple(product.materials or []),
    )


async def publish_to_platforms(
    product: Product,
    platforms: list[str],
    db: AsyncSession,
) -> list[dict]:
    """상품을 선택된 플랫폼에 발행하고 Listing 레코드를 DB에 기록한다.

    Returns:
        플랫폼별 결과 요약 목록 (API 응답에 포함 가능).
    """
    canonical = _to_canonical(product)

    # 사용자가 연동한 플랫폼 계정(토큰/세션) 조회
    acc_result = await db.execute(
        select(PlatformAccount).where(
            PlatformAccount.user_id == product.user_id,
            PlatformAccount.is_active == True,
        )
    )
    credential_map = {a.platform: a.credential_key for a in acc_result.scalars()}

    def _adapter_for(platform: str) -> PlatformAdapter:
        # HTTP API 어댑터(번개 등)는 브라우저 불필요.
        if platform in _API_ADAPTERS:
            return get_adapter(platform)
        # 브라우저 어댑터: 세션 파일로 로그인 상태 주입
        user_session = _AUTH_DIR / "users" / str(product.user_id) / f"{platform}.json"
        dev_session = _AUTH_DIR / f"{platform}.json"
        storage = None
        if user_session.exists():
            storage = str(user_session)
        elif dev_session.exists():
            storage = str(dev_session)
        pb = PlaywrightBrowser(headless=settings.browser_headless, storage_state=storage)
        return get_adapter(platform, pb)

    def _credentials_for(platform: str) -> Credentials:
        # API 어댑터(번개): credential_key = 토큰 → username 에 전달.
        # 브라우저 어댑터: 세션 기반이라 빈 값.
        token = credential_map.get(platform, "")
        return Credentials(username=token, password="")

    try:
        outcomes = await publish_product(
            canonical,
            platforms,
            adapter_for=_adapter_for,
            credentials_for=_credentials_for,
        )
    finally:
        pass

    # Listing 테이블에 기록
    results = []
    any_listed = False
    for outcome in outcomes:
        listing = Listing(
            product_id=product.id,
            platform=outcome.platform,
            platform_product_id=outcome.platform_product_id or "",
            status=(
                ListingStatus.active if outcome.status == PublishStatus.listed
                else ListingStatus.pending
            ),
            listed_at=datetime.utcnow(),
            # platform_account_id 는 계정 연동 후 채움 (임시 product.user_id)
            platform_account_id=product.user_id,
        )
        db.add(listing)
        results.append({
            "platform": outcome.platform,
            "status": outcome.status.value,
            "platform_product_id": outcome.platform_product_id,
            "error": outcome.error,
            "missing_required": outcome.missing_required,
        })
        if outcome.status == PublishStatus.listed:
            any_listed = True

    # 하나라도 등록됐으면 상품 상태를 listed 로 전환
    if any_listed:
        product.status = ProductStatus.listed

    await db.commit()
    return results
