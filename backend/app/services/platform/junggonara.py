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
  - 로그인: 소셜 로그인(네이버/카카오/휴대폰번호) 전용. 아이디/패스워드 폼 없음.
    → 쿠키 기반 세션 주입 방식 사용.
"""

from app.services.platform.base import FormPlatformAdapter
from app.services.platform.forms import (
    FieldKind, FormField, LoginSpec, PlatformFormSpec, PopupSelect,
)


class JunggonaraAdapter(FormPlatformAdapter):
    spec = PlatformFormSpec(
        platform="junggonara",
        login=LoginSpec(
            url="https://web.joongna.com/signin",
            # 중고나라는 소셜 로그인(네이버/카카오) + 휴대폰번호 인증만 지원.
            # 아이디/패스워드 폼이 없으므로 쿠키 세션 주입 방식을 사용한다.
            # 아래 셀렉터는 휴대폰번호 로그인 플로우용 fallback.
            username_selector='input[placeholder*="휴대폰"]',
            password_selector='input[placeholder*="인증번호"]',
            submit_selector='button:has-text("인증요청")',
            success_selector='a[href="/my"], [class*="mypage"], [class*="MyPage"]',
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
                    "택배거래": 'label:has-text("택배거래")',
                    "만나서직거래": 'label:has-text("만나서 직거래")',
                    "세븐일레븐 편의점 픽업": 'label:has-text("세븐일레븐")',
                },
            ),
            # 카테고리는 팝업 트리 선택 방식 → 멀티스텝 핸들러 필요(여기서 제외).
        ),
        image_field=FormField("images", 'input[type="file"]', FieldKind.files),
        submit_selector='button[type="submit"]:has-text("판매하기")',
        # 카테고리: 트리 팝업 방식. 등록 폼에서 카테고리 선택 버튼 클릭 → 모달 트리.
        category_opener='button:has-text("카테고리")',
        category_container='[class*="category"] [class*="modal"], [class*="Category"] [class*="tree"]',
        category_confirm='[class*="category"] button:has-text("선택완료"), [class*="Category"] button:has-text("확인")',
        # 등록 후 상품 ID: 등록 완료 시 /product/{id} 로 리다이렉트됨.
        # URL에서 추출하므로 셀렉터 대신 URL 패턴 사용.
        listing_id_selector="",  # URL 패턴(/product/{id})에서 추출
        listing_id_attribute=None,
        listing_url_template="https://web.joongna.com/product/{id}",
        # 판매완료 판정: 상품 상세 페이지에 "판매완료" 텍스트 배지가 이미지 위에 표시됨.
        sold_selector='[class*="sold"], [class*="Sold"], [class*="status"]:has-text("판매완료")',
        sold_marker="판매완료",
        # 상품 관리(수정/삭제): 내 상품 상세에서 더보기 메뉴 → 삭제
        manage_url_template="https://web.joongna.com/product/{id}",
        delete_selector='button:has-text("삭제"), [class*="more"] button:has-text("삭제")',
        delete_confirm_selector='[class*="modal"] button:has-text("확인"), [class*="confirm"] button:has-text("삭제")',
        # 가격 수정: 수정 페이지에서 가격 필드 재사용
        price_selector="#productPrice",
        save_selector='button[type="submit"]:has-text("수정")',
    )
