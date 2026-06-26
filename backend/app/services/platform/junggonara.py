"""[여원] 중고나라 어댑터 (Playwright 기반).

⚠️ 셀렉터/URL 은 실제 중고나라 웹(web.joongna.com) DOM 분석 후 채워야 한다.
중고나라는 컨디션을 등급이 아닌 상품상태(중고/새상품)로 받고, 구성품·거래방법
같은 고유 필드가 있다(매핑 엔진에서 채워짐).
"""

from app.services.platform.base import FormPlatformAdapter
from app.services.platform.forms import FieldKind, FormField, LoginSpec, PlatformFormSpec


class JunggonaraAdapter(FormPlatformAdapter):
    spec = PlatformFormSpec(
        platform="junggonara",
        login=LoginSpec(
            url="",
            username_selector="",
            password_selector="",
            submit_selector="",
            success_selector="",
        ),
        new_listing_url="",
        fields=(
            FormField("title", ""),
            FormField("category", "", FieldKind.select),
            FormField("price", ""),
            FormField("description", ""),
            FormField("condition", "", FieldKind.select),       # 중고/새상품
            FormField("components", "", FieldKind.select),       # 없음/일부 포함/전체 포함
            FormField("trade_method", "", FieldKind.select),     # 택배/직거래/편의점픽업
        ),
        image_field=FormField("images", "", FieldKind.files),
        submit_selector="",
        listing_id_selector="",
        listing_id_attribute=None,
        listing_url_template="",
        sold_selector="",
        sold_marker="판매완료",
        manage_url_template="",
        delete_selector="",
        delete_confirm_selector="",
    )
