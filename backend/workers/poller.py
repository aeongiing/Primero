"""[여원] 판매 완료 폴링 워커.

각 active 리스팅을 주기적으로 폴링해 판매 완료를 감지하면
sold_sync 를 트리거한다. ECS Fargate 상시 워커 또는 EventBridge +
Lambda 로 배포한다.
"""

import asyncio
import logging
import os
import signal
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import selectinload, sessionmaker

from app.models.listing import Listing, ListingStatus
from app.models.product import ProductStatus
from app.services.automation.sold_sync import sync_sold
from app.services.platform.base import PlatformError
from app.services.platform.browser import BrowserAutomation, Credentials, PlaywrightBrowser
from app.services.platform.registry import get_adapter
from app.services.secrets.manager import load_credentials

# 환경변수 설정
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/primero")
POLLING_INTERVAL_SECONDS = int(os.getenv("POLLING_INTERVAL_SECONDS", "60"))
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Graceful shutdown
shutdown_event = asyncio.Event()


def signal_handler(sig, frame):
    """SIGTERM/SIGINT 핸들러."""
    logger.info("Shutdown signal received, finishing current cycle...")
    shutdown_event.set()


signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


# DB 엔진 및 세션
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def poll_once() -> None:
    """active 리스팅을 1회 폴링한다."""
    logger.info("Polling cycle started")
    
    async with AsyncSessionLocal() as db:
        # 1. 모든 active 리스팅 조회 (Product, PlatformAccount JOIN)
        result = await db.execute(
            select(Listing)
            .join(Listing.product)
            .options(
                selectinload(Listing.product),
                selectinload(Listing.platform_account)
            )
            .where(Listing.status == ListingStatus.active)
            .where(Listing.product.has(ProductStatus != ProductStatus.sold))
        )
        listings = result.scalars().all()
        
        if not listings:
            logger.info("No active listings to poll")
            return
        
        logger.info(f"Polling {len(listings)} active listings")
        
        # 2. 플랫폼별로 그룹핑 (브라우저 재사용)
        listings_by_platform = defaultdict(list)
        for listing in listings:
            listings_by_platform[listing.platform].append(listing)
        
        # 3. 플랫폼별 브라우저 인스턴스 생성 및 폴링
        browsers: dict[str, BrowserAutomation] = {}
        
        for platform, platform_listings in listings_by_platform.items():
            try:
                # 브라우저 생성 (플랫폼별 1회)
                if platform not in browsers:
                    # TODO: storage_state 경로 설정
                    browsers[platform] = PlaywrightBrowser(headless=BROWSER_HEADLESS)
                
                browser = browsers[platform]
                adapter = get_adapter(platform, browser)
                
                # 각 리스팅 확인
                for listing in platform_listings:
                    try:
                        # Secrets Manager에서 credentials 로드
                        credentials = await load_credentials(listing.platform_account.credential_key)
                        
                        is_sold = await adapter.is_sold(credentials, listing.platform_product_id)
                        
                        if is_sold:
                            logger.info(
                                f"Sold detected: listing={listing.id}, "
                                f"platform={listing.platform}, product={listing.product_id}"
                            )
                            
                            # SoldSyncService 호출 (브라우저 재사용)
                            await sync_sold(db, listing.product_id, listing.id, browser)
                    
                    except PlatformError as e:
                        logger.warning(
                            f"Failed to check listing: listing_id={listing.id}, "
                            f"platform={listing.platform}, error={str(e)}"
                        )
                        # 다음 리스팅 계속
                    
                    except Exception as e:
                        logger.error(
                            f"Unexpected error checking listing {listing.id}: {e}",
                            exc_info=True
                        )
            
            except Exception as e:
                logger.error(f"Failed to poll platform {platform}: {e}", exc_info=True)
                # 다음 플랫폼 계속
        
        # 4. 브라우저 정리
        for browser in browsers.values():
            try:
                await browser.close()
            except Exception as e:
                logger.warning(f"Failed to close browser: {e}")
    
    logger.info("Polling cycle completed")


async def run() -> None:
    """폴링 루프 (Fargate 상시 워커용)."""
    logger.info(f"Poller started (interval={POLLING_INTERVAL_SECONDS}s)")
    
    while not shutdown_event.is_set():
        try:
            await poll_once()
        except Exception as e:
            logger.error(f"Polling cycle failed: {e}", exc_info=True)
        
        # 다음 폴링까지 대기 (또는 shutdown 이벤트)
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=POLLING_INTERVAL_SECONDS)
        except asyncio.TimeoutError:
            continue
    
    logger.info("Poller stopped gracefully")


if __name__ == "__main__":
    asyncio.run(run())
