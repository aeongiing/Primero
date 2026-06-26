"""[여원] 매핑 엔진 (순수 함수).

표준_상품 → 플랫폼 페이로드 변환. 외부 의존 없음. 규칙은 config.py 의 선언적
설정에서 읽는다.
"""

from app.domain.mapping.config import ListFieldRule, PlatformConfig, PLATFORM_CONFIGS
from app.domain.mapping.grades import condition_to_grade
from app.domain.mapping.models import CanonicalProduct, MappingResult

# 페이로드에 공통으로 복사하는 스칼라 필드.
_SCALAR_FIELDS = ("title", "brand", "category", "price")


def _dedupe(values: tuple[str, ...]) -> list[str]:
    """입력 순서를 보존하며 중복을 제거한다."""
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def apply_list_rule(values: tuple[str, ...], rule: ListFieldRule) -> tuple[list[str], list[str]]:
    """리스트 필드에 허용목록 검증 + 우선순위 절단을 적용한다.

    Returns:
        (mapped, unmapped)
        - mapped: 허용값 중 대표성 우선순위로 정렬 후 max_count 로 절단한 결과.
        - unmapped: 허용 목록에 없는 값들(수동 선택 요청 대상).
    """
    deduped = _dedupe(values)

    if rule.allowed is None:
        mapped = deduped
        if rule.max_count is not None:
            mapped = mapped[: rule.max_count]
        return mapped, []

    priority = {v: i for i, v in enumerate(rule.allowed)}
    valid = [v for v in deduped if v in priority]
    unmapped = [v for v in deduped if v not in priority]
    valid.sort(key=lambda v: priority[v])
    if rule.max_count is not None:
        valid = valid[: rule.max_count]
    return valid, unmapped


def _is_empty(value) -> bool:
    """필수 필드 충족 여부 판단용. None/빈문자열/0/빈리스트는 미충족."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, tuple)):
        return len(value) == 0
    if isinstance(value, (int, float)):
        return value <= 0
    return False


def map_product(product: CanonicalProduct, platform: str) -> MappingResult:
    """표준_상품을 특정 플랫폼 페이로드로 변환한다.

    매핑 안 되는 값은 unmapped_fields 에, 매핑 후에도 비는 필수 필드는
    missing_required 에 담아 항상 반환한다(등록 보류 판단용).
    """
    config: PlatformConfig | None = PLATFORM_CONFIGS.get(platform)
    if config is None:
        raise ValueError(f"Unknown platform: {platform}")

    result = MappingResult(platform=platform)
    payload: dict = {}

    # 1) 공통 스칼라
    for f in _SCALAR_FIELDS:
        payload[f] = getattr(product, f)

    # 2) 설명 (필요 시 컨디션 본문 포함)
    description = product.description
    if config.fold_condition_into_description:
        grade = condition_to_grade(product.condition)
        description = f"{description}\n\n[컨디션] {grade}"
    payload["description"] = description

    # 3) 사이즈
    if config.size_allowed is None:
        payload["size"] = product.size
    elif product.size in config.size_allowed:
        payload["size"] = product.size
    elif not _is_empty(product.size):
        result.unmapped_fields["size"] = [product.size]  # type: ignore[list-item]

    # 4) 컨디션 등급 (지원 플랫폼만 별도 필드)
    if config.supports_condition_grade:
        payload["condition"] = condition_to_grade(product.condition)

    # 5) 리스트 필드 (플랫폼이 지원하는 것만)
    for field_name, rule in config.list_fields.items():
        values: tuple[str, ...] = getattr(product, field_name, ())
        mapped, unmapped = apply_list_rule(values, rule)
        if mapped:
            payload[field_name] = mapped
        if unmapped:
            result.unmapped_fields[field_name] = unmapped

    # 6) 필수 필드 검증
    for f in config.required:
        if _is_empty(payload.get(f)):
            result.missing_required.append(f)

    result.payload = payload
    return result
