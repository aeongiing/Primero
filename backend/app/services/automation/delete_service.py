"""[여원] 상품 삭제 시 플랫폼 리스팅 일괄 삭제 서비스.

상품 삭제 시 모든 active 리스팅을 플랫폼에서도 삭제한다.
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


async def delete_all_listings(product: Product, db: AsyncSession) -> dict:
    """상품의 모든 active 리스팅을 플랫폼에서 삭제한다.
    
    Returns:
        삭제 결과 요약 (deleted_count, failed_count, failed_platforms)
    """
    active_listings = [l for l in product.listings if l.status == ListingStatus.active]
    
    if not active_listings:
        logger.info(f"Product {product.id}: no active listings to delete")
        return {"deleted_count": 0, "failed_count": 0, "failed_platforms": []}
    
    browser = PlaywrightBrowser(headless=settings.browser_headless)
    deleted_count = 0
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
                
                await adapter.delete_listing(credentials, listing.platform_product_id)
                
                listing.status = ListingStatus.removed
                deleted_count += 1
                logger.info(f"Deleted listing {listing.id} from {listing.platform}")
                
            except PlatformError as e:
                logger.warning(
                    f"Failed to delete listing {listing.id} on {listing.platform}: {e}"
                )
                failed_count += 1
                failed_platforms.append(listing.platform)
            except Exception as e:
                logger.error(f"Unexpected error deleting listing {listing.id}: {e}", exc_info=True)
                failed_count += 1
                failed_platforms.append(listing.platform)
        
        await db.commit()
        
    finally:
        await browser.close()
    
    return {
        "deleted_count": deleted_count,
        "failed_count": failed_count,
        "failed_platforms": failed_platforms,
    }
