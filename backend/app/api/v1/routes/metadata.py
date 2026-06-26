"""플랫폼 입력 메타데이터 API.

프론트 업로드 폼이 카테고리/색상/소재 등 선택지를 동적으로 구성할 수 있도록
`플랫폼 input.md`(SSOT)에서 옮긴 선언적 메타데이터를 노출한다.
"""

from fastapi import APIRouter, HTTPException

from app.domain import platform_metadata as meta
from app.schemas.metadata import (
    CanonicalOptions,
    PlatformInfo,
    PlatformListResponse,
)

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.get(
    "/options",
    response_model=CanonicalOptions,
    summary="정규 입력 옵션 조회",
    description="차란 기준 정규 옵션(컨디션·사이즈·핏·색상·계절·패턴·소재·스타일)과 "
    "선택 개수 제약, 컨디션 점수 매핑을 반환한다.",
)
async def get_canonical_options() -> CanonicalOptions:
    return CanonicalOptions(
        conditions=meta.CONDITIONS,
        sizes=meta.SIZES,
        fits=meta.FITS,
        colors=meta.COLORS,
        seasons=meta.SEASONS,
        patterns=meta.PATTERNS,
        materials=meta.MATERIALS,
        styles=meta.STYLES,
        max_select=meta.MAX_SELECT,
        condition_score_map=meta.CONDITION_SCORE_MAP,
    )


@router.get(
    "/platforms",
    response_model=PlatformListResponse,
    summary="지원 플랫폼 목록",
)
async def list_platforms() -> PlatformListResponse:
    return PlatformListResponse(platforms=meta.SUPPORTED_PLATFORMS)


@router.get(
    "/platforms/{platform}",
    response_model=PlatformInfo,
    summary="플랫폼별 메타데이터 조회",
    description="해당 플랫폼의 필드 지원 여부와 카테고리 트리를 반환한다.",
)
async def get_platform_metadata(platform: str) -> PlatformInfo:
    if platform not in meta.SUPPORTED_PLATFORMS:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": f"지원하지 않는 플랫폼입니다: {platform}",
                "details": {"supported": meta.SUPPORTED_PLATFORMS},
            },
        )
    return PlatformInfo(
        platform=platform,
        field_support=meta.PLATFORM_FIELD_SUPPORT[platform],
        categories=meta.PLATFORM_CATEGORIES[platform],
    )
