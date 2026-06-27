"""[여원] 상품 → 다중 플랫폼 등록 코어 로직.

listing_service.py 에서 호출한다. 매핑 → 브라우저 자동화 → 결과 반환.
부분 실패 격리: 한 플랫폼 실패가 다른 플랫폼을 막지 않는다.
"""
from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from app.domain.mapping import CanonicalProduct, map_product
from app.services.platform.base import ListingPayload, PlatformAdapter, PlatformError
from app.services.platform.browser import Credentials

logger = logging.getLogger(__name__)


class PublishStatus(str, enum.Enum):
    listed = "listed"
    failed = "failed"
    skipped = "skipped"  # 필수 필드 누락 등


@dataclass
class PublishOutcome:
    platform: str
    status: PublishStatus
    platform_product_id: Optional[str] = None
    error: Optional[str] = None
    missing_required: List[str] = field(default_factory=list)


async def publish_product(
    canonical: CanonicalProduct,
    platforms: List[str],
    adapter_for: Callable[[str], PlatformAdapter],
    credentials_for: Callable[[str], Credentials],
    image_paths: tuple = (),
) -> List[PublishOutcome]:
    """표준_상품을 선택된 플랫폼에 순차 등록한다.

    Args:
        canonical: 매핑 엔진 입력(정규 상품).
        platforms: 등록 대상 플랫폼 목록.
        adapter_for: 플랫폼명 → 어댑터 팩토리.
        credentials_for: 플랫폼명 → 자격증명 팩토리.

    Returns:
        플랫폼별 PublishOutcome 리스트.
    """
    outcomes: List[PublishOutcome] = []

    for platform in platforms:
        # 1) 매핑
        mapping = map_product(canonical, platform)
        if not mapping.ok:
            outcomes.append(PublishOutcome(
                platform=platform,
                status=PublishStatus.skipped,
                missing_required=mapping.missing_required,
                error=f"필수 필드 누락: {mapping.missing_required}",
            ))
            continue

        # 2) 브라우저 자동화로 등록
        adapter = adapter_for(platform)
        credentials = credentials_for(platform)
        payload = ListingPayload(
            fields=mapping.payload,
            image_paths=image_paths,
        )

        try:
            product_id = await adapter.create_listing(credentials, payload)
            outcomes.append(PublishOutcome(
                platform=platform,
                status=PublishStatus.listed,
                platform_product_id=product_id,
            ))
            logger.info(f"✅ {platform} 등록 완료: {product_id}")
        except PlatformError as e:
            outcomes.append(PublishOutcome(
                platform=platform,
                status=PublishStatus.failed,
                error=str(e),
            ))
            logger.error(f"❌ {platform} 등록 실패: {e}")
        except Exception as e:
            outcomes.append(PublishOutcome(
                platform=platform,
                status=PublishStatus.failed,
                error=f"예상치 못한 오류: {type(e).__name__}: {e}",
            ))
            logger.error(f"❌ {platform} 예외: {e}")
        finally:
            try:
                await adapter.browser.close()
            except Exception:
                pass

    return outcomes


async def publish_to_platform(
    canonical: CanonicalProduct,
    platform: str,
    adapter_for: Callable[[str], PlatformAdapter],
    credentials_for: Callable[[str], Credentials],
) -> PublishOutcome:
    """단일 플랫폼 등록 (publish_product 의 단건 버전)."""
    results = await publish_product(canonical, [platform], adapter_for, credentials_for)
    return results[0]
