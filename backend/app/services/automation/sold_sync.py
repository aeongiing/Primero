"""[여원] 판매 완료 동기화.

한 플랫폼에서 판매 완료가 감지되면 나머지 플랫폼의 리스팅을 자동
삭제하고 상품 상태를 sold 로 전환한다.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.listing import Listing, ListingStatus
from app.models.product import Product, ProductStatus
from app.models.sale import Sale
from app.services.platform.base import PlatformError
from app.services.platform.browser import BrowserAutomation, Credentials, PlaywrightBrowser
from app.services.platform.registry import get_adapter
from app.services.secrets.manager import load_credentials

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """동기화 결과."""
    product_id: uuid.UUID
    sold_listing_id: uuid.UUID
    deleted_count: int
    failed_count: int
    failed_platforms: list[str]


async def sync_sold(
    db: AsyncSession,
    product_id: uuid.UUID,
    sold_listing_id: uuid.UUID,
    browser: BrowserAutomation | None = None,
) -> SyncResult:
    """판매된 리스팅을 제외한 나머지 플랫폼에서 상품을 삭제한다.
    
    Args:
        db: 데이터베이스 세션
        product_id: 판매된 상품 ID
        sold_listing_id: 판매 완료된 리스팅 ID
        browser: 브라우저 인스턴스 (None이면 새로 생성)
    
    Returns:
        SyncResult: 삭제 성공/실패 개수 및 실패한 플랫폼 목록
    """
    # 1. 동시성 체크: 이미 sold인 경우 조기 반환
    product = await db.get(Product, product_id)
    if not product:
        raise ValueError(f"Product {product_id} not found")
    
    if product.status == ProductStatus.sold:
        logger.info(f"Product {product_id} already sold, skipping")
        return SyncResult(product_id, sold_listing_id, 0, 0, [])
    
    # 2. 판매된 리스팅 조회
    sold_listing = await db.get(Listing, sold_listing_id)
    if not sold_listing:
        raise ValueError(f"Listing {sold_listing_id} not found")
    
    # 3. 트랜잭션: Product/Listing/Sale 업데이트
    product.status = ProductStatus.sold
    sold_listing.status = ListingStatus.sold
    
    sale = Sale(
        product_id=product_id,
        listing_id=sold_listing_id,
        platform=sold_listing.platform,
        sold_at=datetime.utcnow()
    )
    db.add(sale)
    await db.commit()
    
    logger.info(
        f"Sold detected: product={product_id}, listing={sold_listing_id}, "
        f"platform={sold_listing.platform}"
    )
    
    # 4. 나머지 active 리스팅 조회 (sold_listing 제외)
    result = await db.execute(
        select(Listing)
        .options(selectinload(Listing.platform_account))
        .where(Listing.product_id == product_id)
        .where(Listing.status == ListingStatus.active)
        .where(Listing.id != sold_listing_id)
    )
    other_listings = result.scalars().all()
    
    if not other_listings:
        logger.info(f"No other active listings for product {product_id}")
        return SyncResult(product_id, sold_listing_id, 0, 0, [])
    
    # 5. 브라우저 생성 (제공되지 않은 경우)
    should_close_browser = False
    if browser is None:
        browser = PlaywrightBrowser(headless=True)
        should_close_browser = True
    
    # 6. 순차 삭제 (부분 실패 격리)
    deleted_count = 0
    failed_count = 0
    failed_platforms = []
    
    for listing in other_listings:
        try:
            # Secrets Manager에서 credentials 로드
            credentials = await load_credentials(listing.platform_account.credential_key)
            
            adapter = get_adapter(listing.platform, browser)
            await adapter.delete_listing(credentials, listing.platform_product_id)
            
            listing.status = ListingStatus.removed
            await db.commit()
            deleted_count += 1
            
            logger.info(f"Removed listing {listing.id} from {listing.platform}")
            
        except PlatformError as e:
            logger.warning(
                f"Failed to delete listing: listing_id={listing.id}, "
                f"platform={listing.platform}, error={str(e)}"
            )
            failed_count += 1
            failed_platforms.append(listing.platform)
            # 다음 리스팅 계속
        except Exception as e:
            logger.error(
                f"Unexpected error deleting listing {listing.id}: {e}",
                exc_info=True
            )
            failed_count += 1
            failed_platforms.append(listing.platform)
    
    # 7. 브라우저 정리
    if should_close_browser:
        await browser.close()
    
    return SyncResult(
        product_id=product_id,
        sold_listing_id=sold_listing_id,
        deleted_count=deleted_count,
        failed_count=failed_count,
        failed_platforms=failed_platforms
    )
