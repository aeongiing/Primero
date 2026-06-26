"""[윤채린] AI 분석 파이프라인.

Claude 멀티모달 단일 호출 → 플랫폼별 매핑을 수행한다.
"""

from typing import Dict, List

from app.schemas.ai import AIAnalysisResult, PlatformMapping
from app.services.ai.classifier import analyze_with_claude

# ─── 차란 → 번개장터 카테고리 매핑 ───

_CHARAN_TO_BUNJANG: Dict[str, str] = {
    "아우터 > 코트": "아우터 > 코트",
    "아우터 > 재킷": "아우터 > 자켓",
    "아우터 > 점퍼": "아우터 > 점퍼",
    "아우터 > 조끼": "아우터 > 조끼/베스트",
    "아우터 > 집업": "아우터 > 가디건",
    "아우터 > 카디건": "아우터 > 가디건",
    "상의 > 니트": "상의 > 니트/스웨터",
    "상의 > 티셔츠": "상의 > 반팔 티셔츠",
    "상의 > 블라우스/셔츠": "상의 > 셔츠",
    "하의 > 팬츠": "바지 > 면바지",
    "하의 > 스커트": "치마 > 미디 스커트",
    "원피스 > 원피스": "원피스 > 미디 원피스",
    "세트 > 정장세트": "셋업/세트 > 정장/셋업",
    "세트 > 트레이닝 세트": "셋업/세트 > 트레이닝/스웨트 셋업",
}

# ─── 성별 → 중고나라 카테고리 매핑 ───
# 중고나라 웹 의류 카테고리는 단순하다(패션의류 > 여성/남성의류). 공용은 여성의류로 둔다.
_GENDER_TO_JUNGGONARA: Dict[str, str] = {
    "남성": "패션의류 > 남성의류",
    "여성": "패션의류 > 여성의류",
    "공용": "패션의류 > 여성의류",
}

_CHARAN_TO_EBAY: Dict[str, str] = {
    "아우터 > 코트": "Outerwear Coats & Jackets",
    "아우터 > 재킷": "Outerwear Coats & Jackets",
    "아우터 > 점퍼": "Outerwear Coats & Jackets",
    "아우터 > 조끼": "Vests",
    "아우터 > 집업": "Sweaters",
    "아우터 > 카디건": "Sweaters",
    "상의 > 니트": "Sweaters",
    "상의 > 티셔츠": "T-Shirts",
    "상의 > 블라우스/셔츠": "Casual Shirts",
    "하의 > 팬츠": "Pants",
    "하의 > 스커트": "Skirts",
    "원피스 > 원피스": "Dresses",
    "세트 > 정장세트": "Suits",
    "세트 > 트레이닝 세트": "Sweats & Tracksuits",
}


def _map_charan(result: Dict) -> PlatformMapping:
    return PlatformMapping(
        platform="charan",
        category=result["category"],
        title=result["title"],
        description=result["description"],
        extra_fields={
            "colors": result["colors"],
            "season": result["season"],
            "pattern": result["pattern"],
            "materials": result["materials"],
            "style": result["style"],
        },
        missing_required=[f for f in ["소재"] if not result["materials"]],
    )


def _map_bunjang(result: Dict) -> PlatformMapping:
    category = _CHARAN_TO_BUNJANG.get(result["category"], "상의 > 반팔 티셔츠")
    desc = result["description"]
    if result["materials"]:
        desc += f"\n\n소재: {', '.join(result['materials'])}"
    if result["season"]:
        desc += f"\n계절: {', '.join(result['season'])}"
    return PlatformMapping(
        platform="bunjang",
        category=category,
        title=result["title"],
        description=desc,
    )


def _map_karrot(result: Dict) -> PlatformMapping:
    return PlatformMapping(
        platform="karrot",
        category="여성의류",
        title=result["title"],
        description=result["description"],
        missing_required=["가격", "거래희망장소"],
    )


def _map_junggonara(result: Dict) -> PlatformMapping:
    gender = result.get("gender", "공용")
    category = _GENDER_TO_JUNGGONARA.get(gender, "패션의류 > 여성의류")
    desc = result["description"]
    if result.get("materials"):
        desc += f"\n\n소재: {', '.join(result['materials'])}"
    # 중고나라는 컨디션 등급 칸이 없어 상품상태(중고/새상품)는 등록 단계에서 처리한다.
    return PlatformMapping(
        platform="junggonara",
        category=category,
        title=result["title"],
        description=desc,
    )


def _map_ebay(result: Dict) -> PlatformMapping:
    category = _CHARAN_TO_EBAY.get(result["category"], "Other Men's Vintage Clothing")
    return PlatformMapping(
        platform="ebay",
        category=f"Women's Vintage Clothing > {category}",
        title=result["title"][:80],
        description=result["description"],
        missing_required=["condition"],
    )


async def analyze(s3_keys: List[str]) -> AIAnalysisResult:
    """이미지 → Claude 분석 → 플랫폼별 매핑 결과를 반환한다."""
    result = await analyze_with_claude(s3_keys)

    mappings = [
        _map_charan(result),
        _map_bunjang(result),
        _map_karrot(result),
        _map_junggonara(result),
        _map_ebay(result),
    ]

    return AIAnalysisResult(
        title=result.get("title", "중고 의류"),
        brand=result.get("brand", "미상"),
        category=result.get("category", "상의 > 티셔츠"),
        gender=result.get("gender", "공용"),
        description=result.get("description", ""),
        condition=5,
        size=None,
        chest=None,
        total_length=None,
        waist=None,
        hip=None,
        rise=None,
        colors=result.get("colors", ["블랙"]),
        material=result.get("materials", []),
        pattern=result.get("pattern", "무지"),
        style=result.get("style", ["베이직"]),
        season=result.get("season", ["봄", "가을"]),
        platform_mappings=mappings,
    )
