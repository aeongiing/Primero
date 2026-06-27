"""[여원] 상품 발행 서비스 — API 라우트에서 호출하는 진입점.

상품 등록 후 선택된 플랫폼에 발행을 시도하고, 결과를 Listing 테이블에 기록한다.
실제 브라우저 등록이 아직 빈 셀렉터라 실패할 수 있지만, "시도 → 기록" 흐름은
동작한다. 실제 등록이 되면 상품 상태를 listed 로 전환한다.

동기 방식(API 안에서 바로 처리). 나중에 SQS 비동기로 전환 시
이 함수의 호출자만 워커로 옮기면 된다.
"""

import asyncio
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.mapping import CanonicalProduct
from app.models.listing import Listing, ListingStatus
from app.models.product import Product, ProductStatus
from app.services.automation.publisher import publish_product, PublishStatus, PublishOutcome
from app.services.platform.base import PlatformAdapter, ListingPayload
from app.services.platform.browser import Credentials, PlaywrightBrowser
from app.services.platform.registry import get_adapter
from app.core.config import settings
from app.services.media.s3 import download as s3_download

# 세션 파일 디렉터리 (backend/auth/)
_AUTH_DIR = Path(__file__).resolve().parent.parent.parent / "auth"


async def _download_images_to_tempdir(images) -> tuple[list[str], tempfile.TemporaryDirectory]:
    """상품 이미지를 S3에서 임시 디렉터리로 내려받는다. 경로 목록과 tmpdir 반환."""
    tmpdir = tempfile.TemporaryDirectory()
    paths: list[str] = []
    for img in sorted(images, key=lambda x: x.order):
        if not img.s3_key:
            continue
        try:
            data = await s3_download(img.s3_key)
            ext = ".jpg"
            tmp_path = Path(tmpdir.name) / f"{img.order}{ext}"
            tmp_path.write_bytes(data)
            paths.append(str(tmp_path))
        except Exception:
            pass  # 이미지 1장 실패해도 나머지 계속
    return paths, tmpdir


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

    # 브라우저 인스턴스(헤드리스) — 저장된 세션으로 이미 로그인된 상태로 시작.
    # 각 플랫폼별 세션 파일: auth/bunjang.json, auth/junggonara.json
    # 세션 파일이 없으면 발행 시 로그인 실패 → failed 로 기록됨.
    browser = PlaywrightBrowser(headless=settings.browser_headless)

    def _adapter_for(platform: str) -> PlatformAdapter:
        # 사용자별 세션 파일 경로 (platform_accounts 에서 저장한 것)
        user_session = _AUTH_DIR / "users" / str(product.user_id) / f"{platform}.json"
        # fallback: 개발자 공용 세션(기존 save_login.py 로 저장한 것)
        dev_session = _AUTH_DIR / f"{platform}.json"
        storage = None
        if user_session.exists():
            storage = str(user_session)
        elif dev_session.exists():
            storage = str(dev_session)
        pb = PlaywrightBrowser(headless=settings.browser_headless, storage_state=storage)
        return get_adapter(platform, pb)

    def _credentials_for(platform: str) -> Credentials:
        # 세션 기반이라 username/password 불필요. 빈 값 전달(폼 로그인 생략됨).
        return Credentials(username="", password="")

    # S3에서 이미지 임시 다운로드
    image_paths: tuple[str, ...] = ()
    tmpdir = None
    if product.images:
        paths, tmpdir = await _download_images_to_tempdir(product.images)
        image_paths = tuple(paths)

    try:
        outcomes = await publish_product(
            canonical,
            platforms,
            adapter_for=_adapter_for,
            credentials_for=_credentials_for,
            image_paths=image_paths,
        )
    finally:
        if tmpdir:
            tmpdir.cleanup()

    # Listing 테이블에 기록
    # 사용자의 platform_account 조회
    from app.models.platform_account import PlatformAccount
    from sqlalchemy import select as sa_select

    results = []
    any_listed = False
    for outcome in outcomes:
        # 해당 플랫폼의 platform_account_id 조회
        pa_result = await db.execute(
            sa_select(PlatformAccount.id).where(
                PlatformAccount.user_id == product.user_id,
                PlatformAccount.platform == outcome.platform,
            )
        )
        pa_id = pa_result.scalar_one_or_none()

        listing = Listing(
            product_id=product.id,
            platform=outcome.platform,
            platform_product_id=outcome.platform_product_id or "",
            status=(
                ListingStatus.active if outcome.status == PublishStatus.listed
                else ListingStatus.pending
            ),
            listed_at=datetime.utcnow(),
            platform_account_id=pa_id or product.user_id,
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
