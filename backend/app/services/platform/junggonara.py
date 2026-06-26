"""[여원] 중고나라 어댑터 (Playwright 기반).

실제 등록 페이지(https://web.joongna.com/product/form?type=regist) DOM 캡처로
확정한 셀렉터.

확정:
  - 상품명: #product-name
  - 가격:   #productPrice
  - 설명:   #product-description (textarea)
  - 사진:   input[type="file"]
  - 상품상태(중고/새상품): 라디오 #used / #new
  - 구성품(없음/일부/전체):  라디오 #none / #partial / #full
  - 거래방법: 체크박스(라벨 기반 text= 셀렉터)
  - 등록:   button[type="submit"] ("판매하기")

⚠️ 미확정/추가 작업 필요:
  - 카테고리: <select> 가 아니라 버튼→팝업(트리) 선택 방식 → 멀티스텝 핸들러 필요
    (현재 fields 에서 제외). 카테고리 트리가 번개/차란과 완전히 다름.
  - 로그인 페이지 미캡처, 등록 후 상품 ID/판매완료/삭제 화면 미캡처.
"""

from app.services.platform.base import FormPlatformAdapter
from app.services.platform.forms import FieldKind, FormField, LoginSpec, PlatformFormSpec


class JunggonaraAdapter(FormPlatformAdapter):
    spec = PlatformFormSpec(
        platform="junggonara",
        login=LoginSpec(
            url="",                # TODO: 로그인 페이지 캡처 후 채움
            username_selector="",
            password_selector="",
            submit_selector="",
            success_selector="",
        ),
        new_listing_url="https://web.joongna.com/product/form?type=regist",
        fields=(
            FormField("title", "#product-name"),
            FormField("price", "#productPrice"),
            FormField("description", "#product-description"),
            FormField(
                "condition", "", FieldKind.radio,
                options={"중고": "#used", "새상품": "#new"},
            ),
            FormField(
                "components", "", FieldKind.radio,
                options={"없음": "#none", "일부 포함": "#partial", "전체 포함": "#full"},
            ),
            FormField(
                "trade_method", "", FieldKind.radio,
                options={
                    "택배거래": "text=택배거래",
                    "만나서직거래": "text=만나서 직거래",
                    "세븐일레븐 편의점 픽업": "text=세븐일레븐 편의점 픽업",
                },
            ),
            # 카테고리는 팝업 트리 선택 방식 → 멀티스텝 핸들러 필요(여기서 제외).
        ),
        image_field=FormField("images", 'input[type="file"]', FieldKind.files),
        submit_selector='button[type="submit"]',
        category_opener='button:has-text("카테고리")',
        listing_id_selector="",    # TODO: 등록 후 결과 화면 캡처 후 채움
        listing_id_attribute=None,
        listing_url_template="",
        sold_selector="",
        sold_marker="판매완료",
        manage_url_template="",
        delete_selector="",
        delete_confirm_selector="",
    )
