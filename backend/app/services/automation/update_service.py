"""[여원] 상품 수정 시 플랫폼 리스팅 일괄 업데이트 서비스.

가격 변경 시 모든 active 리스팅의 가격을 플랫폼에서도 업데이트한다.
부분 실패 격리: 한 플랫폼 실패가 다른 플랫폼을 막지 않는다.
"""

import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.listing import Listing, ListingStatus
from app.models.product import Product
from app.services.platform.base import PlatformError
from app.services.platform.browser import Credentials, PlaywrightBrowser
from app.services.platform.registry import get_adapter
from app.services.secrets.manager import load_credentials
from app.core.config import settings

logger = logging.getLogger(__name__)

_AUTH_DIR = Path(__file__).resolve().parent.parent.parent / "auth"


async def update_listing_price(product: Product, new_price: int, db: AsyncSession) -> dict:
    """상품의 모든 active 리스팅 가격을 플랫폼에서 업데이트한다.
    
    Args:
        product: 상품
        new_price: 새 가격
        db: 데이터베이스 세션
    
    Returns:
        업데이트 결과 요약 (updated_count, failed_count, failed_platforms)
    """
    active_listings = [l for l in product.listings if l.status == ListingStatus.active]
    
    if not active_listings:
        logger.info(f"Product {product.id}: no active listings to update")
        return {"updated_count": 0, "failed_count": 0, "failed_platforms": []}
    
    browser = PlaywrightBrowser(headless=settings.browser_headless)
    updated_count = 0
    failed_count = 0
    failed_platforms = []
    
    try:
        for listing in active_listings:
            try:
                # 세션 파일 로드
                user_session = _AUTH_DIR / "users" / str(product.user_id) / f"{listing.platform}.json"
                dev_session = _AUTH_DIR / f"{listing.platform}.json"
                storage = None
                if user_session.exists():
                    storage = str(user_session)
                elif dev_session.exists():
                    storage = str(dev_session)
                
                pb = PlaywrightBrowser(headless=settings.browser_headless, storage_state=storage)
                adapter = get_adapter(listing.platform, pb)
                
                # Secrets Manager에서 credentials 로드
                if hasattr(listing, 'platform_account') and listing.platform_account:
                    credentials = await load_credentials(listing.platform_account.credential_key)
                else:
                    credentials = Credentials(username="", password="")
                
                await adapter.update_price(credentials, listing.platform_product_id, new_price)
                
                updated_count += 1
                logger.info(
                    f"Updated price on {listing.platform} for listing {listing.id}: {new_price}"
                )
                
            except PlatformError as e:
                logger.warning(
                    f"Failed to update price for listing {listing.id} on {listing.platform}: {e}"
                )
                failed_count += 1
                failed_platforms.append(listing.platform)
            except Exception as e:
                logger.error(f"Unexpected error updating listing {listing.id}: {e}", exc_info=True)
                failed_count += 1
                failed_platforms.append(listing.platform)
        
        await db.commit()
        
    finally:
        await browser.close()
    
    return {
        "updated_count": updated_count,
        "failed_count": failed_count,
        "failed_platforms": failed_platforms,
    }
