from typing import Dict, List, Optional

from pydantic import BaseModel


class PlatformMapping(BaseModel):
    """단일 플랫폼에 대한 매핑 결과."""
    platform: str
    category: str
    title: str
    description: str
    extra_fields: Dict[str, object] = {}  # 플랫폼 고유 필드 (색상, 계절, 소재 등)
    missing_required: List[str] = []  # 매핑 불가 필수 필드
    unmapped_fields: Dict[str, str] = {}  # 허용목록 매핑 안 된 값


class AIAnalysisResult(BaseModel):
    # 차란 기준 정규(canonical) 분석 결과
    title: str
    brand: str
    category: str
    description: str
    condition: int
    size: Optional[str]
    chest: Optional[int]
    total_length: Optional[int]
    waist: Optional[int]
    hip: Optional[int]
    rise: Optional[int]
    colors: List[str]
    material: List[str]
    pattern: str
    style: List[str]
    season: List[str]

    # 플랫폼별 매핑
    platform_mappings: List[PlatformMapping] = []
