"""[여원] 매핑 도메인 값 객체 (순수).

외부(DB/Pydantic) 타입에 의존하지 않는 입력/출력 표현. API 레이어에서 ORM/
스키마를 이 값 객체로 변환해 엔진에 전달한다.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CanonicalProduct:
    """표준_상품(SSOT)의 매핑 입력 표현.

    값들은 차란 기준 정규값이다. 플랫폼별 축약/변환은 엔진이 수행한다.
    condition 은 0~10 척도(소수 허용).
    """
    title: str
    brand: str
    description: str
    category: str
    condition: float
    price: int
    size: str | None = None
    colors: tuple[str, ...] = ()
    materials: tuple[str, ...] = ()
    seasons: tuple[str, ...] = ()
    patterns: tuple[str, ...] = ()
    styles: tuple[str, ...] = ()


@dataclass
class MappingResult:
    """단일 플랫폼에 대한 매핑 결과.

    - payload: 해당 플랫폼 등록에 사용할 필드 묶음.
    - unmapped_fields: 플랫폼 허용 목록에 매핑되지 않은 값들(필드명 -> 값 목록).
      사용자에게 수동 선택을 요청하기 위해 보존한다.
    - missing_required: 매핑 후에도 비어 있는 필수 필드. 비어 있지 않으면 등록 보류.
    """
    platform: str
    payload: dict = field(default_factory=dict)
    unmapped_fields: dict[str, list[str]] = field(default_factory=dict)
    missing_required: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """등록 가능 여부. 필수 필드가 모두 채워졌을 때 True."""
        return not self.missing_required
