"""[여원] 플랫폼 매핑 엔진.

표준_상품(차란 기준 정규값)을 각 외부 플랫폼이 요구하는 등록 페이로드로
변환한다. 순수 함수로만 구성되며 외부 의존이 없다.
"""

from app.domain.mapping.models import CanonicalProduct, MappingResult
from app.domain.mapping.grades import condition_to_grade
from app.domain.mapping.engine import map_product

__all__ = [
    "CanonicalProduct",
    "MappingResult",
    "condition_to_grade",
    "map_product",
]
