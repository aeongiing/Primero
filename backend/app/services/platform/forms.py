"""[여원] 플랫폼 등록 폼 선언적 스펙.

각 플랫폼의 로그인/등록/조회/삭제 화면을 "셀렉터 데이터"로 기술한다. 코드가
아닌 설정이므로, 신규 플랫폼은 PlatformFormSpec 추가만으로 지원한다.

⚠️ 셀렉터 값은 각 플랫폼의 실제 DOM 분석 후 채워야 한다. 현재는 구조만 잡고
빈 문자열("")로 둔 placeholder 이며, 실제 발행 동작 전 반드시 확정해야 한다.
매핑/오케스트레이션 로직은 이 값과 무관하게 테스트로 검증된다.
"""

from dataclasses import dataclass
from enum import Enum


class FieldKind(str, Enum):
    """입력 방식."""
    fill = "fill"        # 텍스트 입력
    select = "select"    # 드롭다운 선택
    files = "files"      # 파일 업로드


@dataclass(frozen=True)
class FormField:
    """등록 폼의 단일 필드.

    - key: 매핑 엔진 payload 의 키(예: "title", "price", "category").
    - selector: 해당 입력 요소의 셀렉터(실제 DOM 확정 필요).
    - kind: 입력 방식.
    """
    key: str
    selector: str
    kind: FieldKind = FieldKind.fill


@dataclass(frozen=True)
class LoginSpec:
    """로그인 화면 스펙."""
    url: str
    username_selector: str
    password_selector: str
    submit_selector: str
    success_selector: str  # 로그인 성공 판정용(이 요소가 보이면 성공)


@dataclass(frozen=True)
class PlatformFormSpec:
    """플랫폼 1개의 전체 자동화 스펙."""
    platform: str
    login: LoginSpec
    # 등록
    new_listing_url: str
    fields: tuple[FormField, ...]
    image_field: FormField | None
    submit_selector: str
    listing_id_selector: str
    listing_id_attribute: str | None = None  # None 이면 text, 아니면 해당 attribute 값
    # 판매 여부 조회
    listing_url_template: str = ""           # "{id}" 치환
    sold_selector: str = ""
    sold_marker: str = ""                    # 이 텍스트가 포함되면 판매완료
    # 삭제
    manage_url_template: str = ""            # "{id}" 치환
    delete_selector: str = ""
    delete_confirm_selector: str = ""
