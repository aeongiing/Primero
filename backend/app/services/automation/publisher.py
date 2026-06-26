from __future__ import annotations
"""[여원] 상품 → 다중 플랫폼 발행 오케스트레이션.

상품 하나를 선택된 플랫폼들에 올리는 "절차"를 지휘한다:
  매핑(번역) → 필수값 검사(보류 판단) → 어댑터로 등록 → 결과 보고.

핵심 원칙(부분 실패 격리): 한 플랫폼이 실패해도 나머지 플랫폼 발행은 계속한다.

외부 의존(어댑터/자격증명)은 호출자가 주입한다. 따라서 이 함수 자체는 실제
사이트 없이 가짜를 주입해 테스트할 수 있다. DB 기록은 호출자(라우트/워커)가
이 결과(PublishOutcome 목록)를 보고 수행한다.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from enum import Enum

from app.domain.mapping import CanonicalProduct, map_product
from app.services.platform.base import ListingPayload, PlatformAdapter
from app.services.platform.browser import Credentials


class PublishStatus(str, Enum):
    """플랫폼 1곳에 대한 발행 결과 상태."""
    listed = "listed"   # 등록 성공
    held = "held"       # 필수값 부족 → 등록 보류
    failed = "failed"   # 등록 시도 중 오류


@dataclass
class PublishOutcome:
    """플랫폼 1곳의 발행 결과."""
    platform: str
    status: PublishStatus
    platform_product_id: str | None = None
    missing_required: list[str] = field(default_factory=list)
    unmapped_fields: dict[str, list[str]] = field(default_factory=dict)
    error: str | None = None


async def publish_to_platform(
    product: CanonicalProduct,
    platform: str,
    adapter_for: Callable[[str], PlatformAdapter],
    credentials_for: Callable[[str], Credentials],
    image_paths: tuple[str, ...] = (),
) -> PublishOutcome:
    """단일 플랫폼에 발행한다. 예외를 잡아 항상 PublishOutcome 으로 반환한다."""
    mapping = map_product(product, platform)

    # 필수값이 비면 등록하지 않고 보류(사용자 보완 필요).
    if not mapping.ok:
        return PublishOutcome(
            platform=platform,
            status=PublishStatus.held,
            missing_required=mapping.missing_required,
            unmapped_fields=mapping.unmapped_fields,
        )

    try:
        adapter = adapter_for(platform)
        credentials = credentials_for(platform)
        payload = ListingPayload(fields=mapping.payload, image_paths=image_paths)
        platform_product_id = await adapter.create_listing(credentials, payload)
    except Exception as exc:  # 한 플랫폼 실패가 다른 플랫폼을 막지 않도록 격리
        return PublishOutcome(
            platform=platform,
            status=PublishStatus.failed,
            unmapped_fields=mapping.unmapped_fields,
            error=str(exc),
        )

    return PublishOutcome(
        platform=platform,
        status=PublishStatus.listed,
        platform_product_id=platform_product_id,
        unmapped_fields=mapping.unmapped_fields,
    )


async def publish_product(
    product: CanonicalProduct,
    platforms: Sequence[str],
    adapter_for: Callable[[str], PlatformAdapter],
    credentials_for: Callable[[str], Credentials],
    image_paths: tuple[str, ...] = (),
) -> list[PublishOutcome]:
    """선택된 모든 플랫폼에 순차 발행하고 플랫폼별 결과 목록을 반환한다.

    각 플랫폼은 독립적으로 처리되어, 한 곳의 보류/실패가 다른 곳을 막지 않는다.
    """
    outcomes: list[PublishOutcome] = []
    for platform in platforms:
        outcome = await publish_to_platform(
            product, platform, adapter_for, credentials_for, image_paths
        )
        outcomes.append(outcome)
    return outcomes
