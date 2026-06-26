from __future__ import annotations
"""플랫폼 메타데이터 응답 스키마 (Swagger 문서화용)."""

from pydantic import BaseModel, Field


class ConditionMapping(BaseModel):
    grade: str = Field(..., examples=["Very-good"])
    min: float = Field(..., description="컨디션 점수 하한", examples=[6.5])
    max: float = Field(..., description="컨디션 점수 상한", examples=[7.9])


class CanonicalOptions(BaseModel):
    """정규(canonical) 입력 옵션 — 차란 기준."""

    conditions: list[str] = Field(..., description="컨디션 등급 (차란)")
    sizes: list[str] = Field(..., description="라벨 사이즈")
    fits: list[str] = Field(..., description="핏감")
    colors: list[str] = Field(..., description="대표 색상")
    seasons: list[str] = Field(..., description="계절 (최대 4개 선택)")
    patterns: list[str] = Field(..., description="패턴")
    materials: list[str] = Field(..., description="소재 (최대 4개 선택)")
    styles: list[str] = Field(..., description="스타일")
    max_select: dict[str, int] = Field(..., description="최대 선택 개수 제약")
    condition_score_map: list[ConditionMapping] = Field(
        ..., description="컨디션 점수(0~10) → 등급 매핑"
    )


class PlatformInfo(BaseModel):
    """플랫폼 단위 메타데이터."""

    platform: str = Field(..., examples=["charan"])
    field_support: dict[str, bool] = Field(..., description="필드 지원 여부")
    categories: dict | list = Field(..., description="카테고리 트리 (플랫폼별 구조 상이)")


class PlatformListResponse(BaseModel):
    platforms: list[str] = Field(..., examples=[["charan", "bunjang", "karrot", "ebay"]])
