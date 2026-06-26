"""[여원] 미판매 자동 할인.

등록 후 1주일간 미판매 상품의 가격을 10% 인하하고 연동된 모든
플랫폼에 변경을 반영한다. EventBridge 스케줄로 주기 실행.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.models.listing import Listing, ListingStatus
from app.models.product import Product, ProductStatus
from app.services.platform.base import PlatformError
from app.services.platform.browser import PlaywrightBrowser
from app.services.platform.registry import get_adapter
from app.services.secrets.manager import load_credentials

logger = logging.getLogger(__name__)


async def apply_weekly_discount() -> int:
    """1주 이상 미판매 상품에 10% 할인을 적용한다.

    Returns:
        할인이 적용된 상품 수.
    """
    async for db in get_async_session():
        # 1. 7일 이상 listed 상태인 상품 조회
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        result = await db.execute(
            select(Product)
            .options(selectinload(Product.listings))
            .where(Product.status == ProductStatus.listed)
            .where(Product.created_at <= seven_days_ago)
        )
        products = result.scalars().all()
        
        if not products:
            logger.info("No products eligible for weekly discount")
            return 0
        
        logger.info(f"Found {len(products)} products eligible for discount")
        
        # 2. 브라우저 인스턴스 생성 (플랫폼별 재사용)
        browser = PlaywrightBrowser(headless=True)
        discounted_count = 0
        
        try:
            for product in products:
                try:
                    # 가격 10% 할인
                    old_price = product.price
                    new_price = round(old_price * 0.9)
                    
                    if new_price == old_price:
                        logger.warning(f"Product {product.id}: price unchanged after discount")
                        continue
                    
                    product.price = new_price
                    await db.commit()
                    
                    logger.info(
                        f"Product {product.id}: price {old_price} -> {new_price} "
                        f"(-{old_price - new_price})"
                    )
                    
                    # 3. 각 active 리스팅에 가격 변경 반영
                    active_listings = [
                        l for l in product.listings 
                        if l.status == ListingStatus.active
                    ]
                    
                    if not active_listings:
                        logger.warning(f"Product {product.id}: no active listings")
                        discounted_count += 1
                        continue
                    
                    # 플랫폼별로 가격 업데이트 (부분 실패 격리)
                    for listing in active_listings:
                        try:
                            # Secrets Manager에서 credentials 로드
                            # listing.platform_account를 eager load
                            await db.refresh(listing, ['platform_account'])
                            credentials = await load_credentials(
                                listing.platform_account.credential_key
                            )
                            
                            adapter = get_adapter(listing.platform, browser)
                            await adapter.update_price(
                                credentials, 
                                listing.platform_product_id, 
                                new_price
                            )
                            
                            logger.info(
                                f"Updated price on {listing.platform} for "
                                f"listing {listing.id}"
                            )
                            
                        except PlatformError as e:
                            logger.warning(
                                f"Failed to update price on {listing.platform}: "
                                f"listing_id={listing.id}, error={str(e)}"
                            )
                            # 다음 플랫폼 계속
                        except Exception as e:
                            logger.error(
                                f"Unexpected error updating listing {listing.id}: {e}",
                                exc_info=True
                            )
                    
                    discounted_count += 1
                    
                except Exception as e:
                    logger.error(
                        f"Failed to apply discount to product {product.id}: {e}",
                        exc_info=True
                    )
                    # 다음 상품 계속
            
            logger.info(f"Applied discount to {discounted_count} products")
            return discounted_count
            
        finally:
            await browser.close()
