"""[여원] 번개장터 어댑터 (Playwright 기반).

실제 등록 페이지(https://m.bunjang.co.kr/products/new) DOM 캡처로 확정한 셀렉터.

확정(단순 입력):
  - 상품명: input[name="common.name"]
  - 설명:   textarea[placeholder^="브랜드, 모델명"]
  - 가격:   input[placeholder^="가격을 입력"]
  - 사진:   #media-input (type=file)
  - 등록:   button[type="submit"] ("등록하기")

⚠️ 미확정/추가 작업 필요:
  - 카테고리/상품상태: <select> 가 아니라 버튼→팝업(모달) 선택 방식이라 단순
    select_option 으로 처리 불가. 별도 멀티스텝 핸들러 필요(현재 fields 에서 제외).
  - 로그인: 번개장터는 전화번호 인증(SMS OTP) 기반. 자동화에서는 저장된
    storage_state(쿠키/세션) 로 로그인을 우회한다. login spec 은 폼 로그인
    폴백용으로 제공하되, 실제 운영은 세션 기반을 권장.
  - 등록 후 상품 ID: 등록 성공 시 /products/{id} 로 리다이렉트되며 URL에서 추출.
  번개는 컨디션 등급 칸이 없어 컨디션은 description 에 포함된다(매핑 엔진 처리).
"""

from app.services.platform.base import FormPlatformAdapter
from app.services.platform.forms import (
    FieldKind, FormField, LoginSpec, PlatformFormSpec, PopupSelect,
)


class BunjangAdapter(FormPlatformAdapter):
    spec = PlatformFormSpec(
        platform="bunjang",
        login=LoginSpec(
            # 번개장터는 전화번호 + SMS OTP 인증. 폼 로그인은 폴백용.
            # 운영 시에는 storage_state(브라우저 세션 파일) 사용 권장.
            url="https://m.bunjang.co.kr/login",
            username_selector='input[placeholder*="전화번호"]',
            password_selector='input[placeholder*="인증번호"]',
            submit_selector='button[class*="_submitBtn_"]',
            success_selector='a[href="/my"]',
        ),
        new_listing_url="https://m.bunjang.co.kr/products/new",
        fields=(
            FormField("title", 'input[name="common.name"]'),
            FormField("description", 'textarea[placeholder^="브랜드, 모델명"]'),
            FormField("price", 'input[placeholder^="가격을 입력"]'),
            # 카테고리/상품상태는 팝업 선택 방식 → 멀티스텝 핸들러 필요(여기서 제외).
        ),
        image_field=FormField("images", "#media-input", FieldKind.files),
        submit_selector='button[type="submit"]',
        # 카테고리: 폼 내 #scroll-categoryId 영역의 li 항목을 정확한 텍스트로 단계 클릭.
        # 헤더 메뉴(여성의류 등)와 텍스트가 겹쳐도 컨테이너 스코프로 충돌을 피한다.
        category_container="#scroll-categoryId",
        # 상품상태: 버튼 누르면 뜨는 드롭다운에서 선택(번개 5단계).
        #   새 상품 (미사용) / 사용감 없음 / 사용감 적음 / 사용감 많음 / 고장/파손 상품
        # 사이즈는 카테고리 선택 후에야 나타나 의존성이 있어 추후 처리.
        popup_selects=(
            PopupSelect("condition", "#scroll-condition button", "#scroll-condition"),
            # 사이즈: 카테고리 선택 후 나타남. 옵션 패널은 포털로 떠서 _valueList 로 스코프.
            # S 가 XS/2XS 에 포함되므로 정확 일치(exact)로 클릭.
            PopupSelect("size", "#scroll-option button", 'ul[class*=_valueList_]', exact=True,
                        confirm='[class*=_panel_] button:has-text("완료")'),
        ),
        # 등록 후: /products/{id} 로 리다이렉트됨. URL 에서 ID 파싱하는 게 가장 신뢰도 높지만,
        # DOM 셀렉터 기반으로도 상품 상세 페이지에서 data-pid 속성으로 추출 가능.
        listing_id_selector='[data-pid]',
        listing_id_attribute="data-pid",
        listing_url_template="https://m.bunjang.co.kr/products/{id}",
        sold_selector='div[class*="_statusBadge_"], span[class*="_saleBadge_"]',
        sold_marker="판매완료",
        manage_url_template="https://m.bunjang.co.kr/products/{id}/edit",
        delete_selector='button:has-text("삭제")',
        delete_confirm_selector='button[class*="_confirmBtn_"]:has-text("확인")',
        # 가격 변경 (수정 페이지에서)
        price_selector='input[placeholder^="가격을 입력"]',
        save_selector='button[type="submit"]:has-text("수정")',
    )
