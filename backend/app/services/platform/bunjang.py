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
  - 로그인: 로그인 페이지 미캡처(소셜/휴대폰 인증 가능성). login 스펙 비움.
  - 등록 후 상품 ID 추출, 판매완료 판정(sold), 삭제 흐름: 해당 화면 미캡처.
  번개는 컨디션 등급 칸이 없어 컨디션은 description 에 포함된다(매핑 엔진 처리).
"""

from app.services.platform.base import FormPlatformAdapter
from app.services.platform.forms import FieldKind, FormField, LoginSpec, PlatformFormSpec


class BunjangAdapter(FormPlatformAdapter):
    spec = PlatformFormSpec(
        platform="bunjang",
        login=LoginSpec(
            url="",                # TODO: 로그인 페이지 캡처 후 채움
            username_selector="",
            password_selector="",
            submit_selector="",
            success_selector="",
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
        # ⚠️ 카테고리 자동 클릭은 헤더 메뉴와 텍스트가 겹쳐 오작동(상품목록으로 이동) →
        #    스코프된 셀렉터 확보 전까지 비활성. 카테고리는 수동 선택.
        category_opener="",
        listing_id_selector="",    # TODO: 등록 후 결과 화면 캡처 후 채움
        listing_id_attribute=None,
        listing_url_template="",
        sold_selector="",
        sold_marker="판매완료",
        manage_url_template="",
        delete_selector="",
        delete_confirm_selector="",
    )
