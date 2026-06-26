"""[여원] 플랫폼 매핑 선언적 설정.

코드가 아닌 데이터로 매핑 규칙을 둔다. 신규 플랫폼은 여기 PlatformConfig 를
추가하는 것만으로 지원한다(엔진 코드 수정 불필요).

허용값/필드의 단일 출처는 steering 의 `플랫폼 input.md` 다. 추측하지 않는다.
카테고리 트리는 방대해 점진 등록 대상이며, allowed=None 은 '검증 보류(자유값)'를
의미한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ListFieldRule:
    """리스트형 필드(색상·소재·계절 등)의 매핑 규칙.

    - allowed: 플랫폼 허용값 집합(순서 = 대표성 우선순위). None 이면 검증/절단 없음.
    - max_count: 최대 선택 개수. None 이면 제한 없음.
    """
    allowed: tuple[str, ...] | None = None
    max_count: int | None = None


@dataclass(frozen=True)
class PlatformConfig:
    """단일 플랫폼의 매핑 설정."""
    name: str
    # payload 에 채워야 하며 비면 missing_required 로 보고할 필드.
    required: tuple[str, ...] = ()
    # 컨디션 등급 필드 지원 여부(차란만 True).
    supports_condition_grade: bool = False
    # 컨디션을 중고/새상품 2단계로 표기(중고나라).
    condition_as_new_used: bool = False
    # 등급 칸이 없는 플랫폼(번개)에서 컨디션을 설명 본문에 포함할지.
    fold_condition_into_description: bool = False
    # size 허용값(차란 S/M/L). None 이면 자유 문자열.
    size_allowed: tuple[str, ...] | None = None
    # 리스트형 필드 규칙. 여기 없는 리스트 필드는 해당 플랫폼에서 미지원(드롭).
    list_fields: dict[str, ListFieldRule] = field(default_factory=dict)
    # 플랫폼 고유 정적 기본값(예: 중고나라 구성품/거래방법). payload 에 없을 때만 채운다.
    defaults: dict = field(default_factory=dict)


# ---- 허용값 집합 (플랫폼 input.md, 차란 기준) -------------------------------

_CHARAN_COLORS = (
    "블랙", "차콜", "레드", "화이트", "그레이", "네이비", "아이보리", "베이지",
    "카키", "민트", "그린", "블루", "스카이 블루", "퍼플", "라벤더", "와인",
    "핑크", "옐로우", "오렌지", "브라운",
)
_CHARAN_MATERIALS = (
    "면", "폴리에스터", "폴리우레탄", "스판덱스", "데님", "리넨", "울", "천연가죽",
    "인조가죽", "천연퍼", "인조퍼", "캐시미어", "앙고라", "알파카", "코듀로이",
    "나일론", "실크", "레이온", "모달", "기모", "모헤어", "엘라스틴", "아크릴",
    "덕다운", "구스다운", "스웨이드",
)
_CHARAN_SEASONS = ("봄", "여름", "가을", "겨울")
_CHARAN_PATTERNS = (
    "무지", "그래픽", "레터링", "스트라이프", "체크", "도트", "플라워",
    "페이즐리", "지브라", "레오파드", "타이다이",
)
_CHARAN_STYLES = (
    "스포티", "스트릿", "베이직", "러블리", "오피스", "캠퍼스", "청순", "섹시",
)


# ---- 플랫폼별 설정 ----------------------------------------------------------

CHARAN = PlatformConfig(
    name="charan",
    required=("title", "brand", "category", "description", "price", "size", "condition"),
    supports_condition_grade=True,
    size_allowed=("S", "M", "L"),
    list_fields={
        "colors": ListFieldRule(allowed=_CHARAN_COLORS, max_count=1),      # 대표 색상 1
        "materials": ListFieldRule(allowed=_CHARAN_MATERIALS, max_count=4),
        "seasons": ListFieldRule(allowed=_CHARAN_SEASONS, max_count=4),
        "patterns": ListFieldRule(allowed=_CHARAN_PATTERNS, max_count=1),
        "styles": ListFieldRule(allowed=_CHARAN_STYLES, max_count=1),
    },
)

BUNJANG = PlatformConfig(
    name="bunjang",
    required=("title", "category", "description", "price"),
    supports_condition_grade=False,
    fold_condition_into_description=True,  # 등급 칸 없음 → 설명에 포함
)

KARROT = PlatformConfig(
    name="karrot",
    required=("title", "category", "description", "price"),
    supports_condition_grade=False,
    size_allowed=None,  # 사이즈는 자유 문자열
)

FRUITS = PlatformConfig(
    name="fruits",
    required=("title", "category", "description", "price"),
    supports_condition_grade=False,
)


JUNGGONARA = PlatformConfig(
    name="junggonara",
    required=("title", "category", "description", "price", "condition"),
    condition_as_new_used=True,   # 상품상태: 중고/새상품
    defaults={
        "components": "없음",      # 구성품 기본값
        "trade_method": "택배거래",  # 거래방법 기본값
    },
)


PLATFORM_CONFIGS: dict[str, PlatformConfig] = {
    CHARAN.name: CHARAN,
    BUNJANG.name: BUNJANG,
    KARROT.name: KARROT,
    FRUITS.name: FRUITS,
    JUNGGONARA.name: JUNGGONARA,
}

# 현재 실제 발행 대상(웹 등록 가능). 당근/차란/fruits 는 앱 전용이라 비활성,
# eBay 는 추후 대상. 설정/어댑터는 남겨두되 이 목록으로만 발행을 허용한다.
ACTIVE_PLATFORMS: tuple[str, ...] = ("bunjang", "junggonara")


def is_active(platform: str) -> bool:
    """현재 발행 가능한(활성) 플랫폼인지 여부."""
    return platform in ACTIVE_PLATFORMS
